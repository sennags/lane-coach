"""Simulated Riot responses; these tests do not contact the authenticated API."""
import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from lane_coach import create_app
from lane_coach.riot import RiotClient, RiotError
from lane_coach.statistics import StatisticsService, StatisticsStore, summarize_match


CATALOG = {'patch': '16.20.1', 'champions': {'777': 'Yone', '103': 'Ahri'},
           'items': {'3031': {'name': 'Gume do Infinito', 'gold': 3450}}}


class Clock:
    now = 1800000000

    def __call__(self):
        return self.now


def documents(index=1, kills=(), own_won=True):
    people = []
    for pid in range(1, 11):
        people.append({'participantId': pid, 'championId': 777 if pid <= 5 else 103,
                       'teamId': 100 if pid <= 5 else 200,
                       'teamPosition': ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'][(pid-1) % 5],
                       'win': own_won if pid <= 5 else not own_won, 'item0': 3031,
                       'puuid': 'do-not-persist-player', 'riotIdGameName': 'do-not-persist-name'})
    match_id = f'BR1_{index}'
    match = {'metadata': {'matchId': match_id}, 'info': {
        'participants': people, 'queueId': 420, 'mapId': 11, 'gameVersion': '16.20.999',
        'gameDuration': 1800, 'gameStartTimestamp': 1799990000000, 'gameEndedInEarlySurrender': False}}
    timeline = {'metadata': {'matchId': match_id}, 'info': {'frames': [
        {'timestamp': 0, 'events': list(kills)}, {'timestamp': 1800000, 'events': []}]}}
    return match, timeline


def kill(killer=3, victim=8, timestamp=120000, assistants=()):
    return {'type': 'CHAMPION_KILL', 'killerId': killer, 'victimId': victim,
            'timestamp': timestamp, 'assistingParticipantIds': list(assistants)}


def test_percentages_count_games_not_events_and_reverse(tmp_path):
    clock = Clock()
    store = StatisticsStore(tmp_path / 'stats.sqlite3', clock)
    matches = [documents(1, [kill(), kill(timestamp=140000), kill(victim=7), kill(8, 3, 900001)]),
               documents(2, [kill(8, 3, assistants=[6])]),
               documents(3, [kill(assistants=[2]), kill(8, 3)]), documents(4)]
    for match, timeline in matches:
        summary = summarize_match(match, timeline, CATALOG)
        store.add(summary)
        store.add(summary)  # Repeated discovery through another player must not double-count.
    result = store.snapshot('Yone', 'Ahri', 'mid', CATALOG)
    assert result['sample'] == 4 and result['state'] == 'insufficient'
    assert result['sides'][0]['kill_pct'] == 50
    assert result['sides'][0]['death_pct'] == 50
    assert result['sides'][0]['unassisted_pct'] == 25
    assert result['sides'][0]['items'] == []
    reverse = store.snapshot('Ahri', 'Yone', 'mid', CATALOG)
    assert reverse['sides'][0] == result['sides'][1]
    assert store.snapshot('Yone', 'Ahri', 'support', CATALOG)['sides'][0]['kill_pct'] == 0
    with store.connection() as con:
        saved = ''.join(r['summary'] for r in con.execute('SELECT summary FROM sample_matches'))
        assert 'puuid' not in saved and 'do-not-persist' not in saved and 'riotId' not in saved


@pytest.mark.parametrize('change', ['queue', 'patch', 'short', 'remake', 'region'])
def test_other_scopes_do_not_enter_sample(change):
    match, timeline = documents()
    if change == 'queue': match['info']['queueId'] = 450
    if change == 'patch': match['info']['gameVersion'] = '16.19.1'
    if change == 'short': match['info']['gameDuration'] = 899
    if change == 'remake': match['info']['gameEndedInEarlySurrender'] = True
    if change == 'region': match['metadata']['matchId'] = 'NA1_1'
    assert summarize_match(match, timeline, CATALOG) is None


@pytest.mark.parametrize('change', ['timeline_id', 'incomplete_timeline', 'event', 'duplicate_person'])
def test_corrupt_timelines_are_rejected(change):
    match, timeline = documents(kills=[kill()])
    if change == 'timeline_id': timeline['metadata']['matchId'] = 'BR1_99'
    if change == 'incomplete_timeline': timeline['info']['frames'][-1]['timestamp'] = 899000
    if change == 'event': timeline['info']['frames'][0]['events'][0]['victimId'] = 20
    if change == 'duplicate_person': match['info']['participants'][1]['participantId'] = 1
    with pytest.raises(RiotError, match='invalid_response'):
        summarize_match(match, timeline, CATALOG)


def seed(store, count=30):
    for i in range(count):
        events = [kill()] if i < 20 else [kill(8, 3)] if i < 25 else []
        store.add(summarize_match(*documents(i + 1, events, i % 2 == 0), CATALOG))


def test_persistence_builds_and_evidence_threshold(tmp_path):
    clock = Clock()
    path = tmp_path / 'stats.sqlite3'
    store = StatisticsStore(path, clock)
    seed(store)
    restarted = StatisticsStore(path, clock)
    result = restarted.snapshot('Yone', 'Ahri', 'mid', CATALOG)
    assert result['state'] == 'ready'
    assert result['sides'][0]['tendency'] == 'Abates mais frequentes'
    assert result['sides'][1]['tendency'] == 'Mortes mais frequentes'
    assert result['sides'][0]['items'][0] == {'id': '3031', 'name': 'Gume do Infinito',
                                            'count': 30, 'frequency': 100.0, 'win_rate': 50.0}
    clock.now += 31 * 86400
    assert restarted.snapshot('Yone', 'Ahri', 'mid', CATALOG)['sample'] == 0


def test_atomic_quota_and_lease_survive_restart(tmp_path):
    clock = Clock()
    path = tmp_path / 'stats.sqlite3'
    store = StatisticsStore(path, clock)
    with ThreadPoolExecutor(max_workers=8) as pool:
        claimed = list(pool.map(lambda _: store.claim(), range(12)))
    assert claimed.count(0) == 1 and claimed.count(None) == 11
    assert StatisticsStore(path, clock).claim() is None
    store.finish(RiotError('rate_limited', 300))
    clock.now += 299
    assert store.claim() is None
    clock.now += 1
    assert store.claim() == 1
    for batch in range(5):
        for _ in range(18):
            store.reserve()
        clock.now += 1
    with pytest.raises(RiotError, match='rate_limited'):
        StatisticsStore(path, clock).reserve()
    clock.now += 120
    store.reserve()


def test_concurrent_requests_cannot_exceed_short_quota(tmp_path):
    store = StatisticsStore(tmp_path / 'stats.sqlite3', Clock())
    def reserve(_):
        try:
            store.reserve()
            return True
        except RiotError:
            return False
    with ThreadPoolExecutor(max_workers=10) as pool:
        assert sum(pool.map(reserve, range(30))) == 18


def test_provider_failure_preserves_ready_cache_and_lease(tmp_path):
    catalog_path = tmp_path / 'catalog.json'
    catalog_path.write_text(json.dumps(CATALOG), encoding='utf-8')
    clock = Clock()
    service = StatisticsService(tmp_path / 'stats.sqlite3', 'test-secret', catalog_path, clock)
    seed(service.store)
    clock.now += 7 * 3600
    service.client.get = lambda *args, **kwargs: (_ for _ in ()).throw(RiotError('rate_limited', 321))
    cursor = service.store.claim()
    service.run(cursor)
    result = service.request('Yone', 'Ahri', 'mid')
    assert result['state'] == 'ready' and result['sample'] == 30
    assert result['provider_issue'] and not result['updating']
    assert service.store.claim() is None


def test_selection_schedules_only_one_background_collection(tmp_path, monkeypatch):
    app = create_app({'TESTING': True, 'RIOT_API_KEY': 'test-secret',
                      'DATABASE': str(tmp_path / 'legacy.sqlite3')})
    starts = []
    class Thread:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def start(self):
            starts.append(self.kwargs)
    monkeypatch.setattr('lane_coach.statistics.threading.Thread', Thread)
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert client.get('/?champion=Unknown&opponent=Ahri&lane=mid').status_code == 400
    assert not starts
    assert client.get('/matchup?champion=Yone&opponent=Ahri&lane=mid').status_code == 200
    assert client.get('/api/statistics?champion=Yone&opponent=Ahri&lane=mid').json['state'] == 'loading'
    assert len(starts) == 1


def test_broken_statistics_database_does_not_hide_champion_guide(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'legacy.sqlite3')})
    with app.extensions['statistics'].store.connection() as con:
        con.execute('DROP TABLE sample_matches')
    client = app.test_client()
    response = client.get('/matchup?champion=Yone&opponent=Ahri&lane=mid')
    assert response.status_code == 200
    assert response.text.count('class="ability-entry"') == 10
    assert 'Estatísticas temporariamente indisponíveis.' in response.text
    assert client.get('/api/statistics?champion=Yone&opponent=Ahri&lane=mid').status_code == 503


def test_testing_does_not_inherit_live_credentials_or_statistics_path(tmp_path, monkeypatch):
    live_path = tmp_path / 'live-statistics.sqlite3'
    monkeypatch.setenv('STATISTICS_DATABASE', str(live_path))
    monkeypatch.setenv('RIOT_API_KEY', 'do-not-use-live-key')
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test/legacy.sqlite3')})
    service = app.extensions['statistics']
    assert not service.key
    assert service.store.path != str(live_path)
    assert not live_path.exists()


@pytest.mark.parametrize('failure', ['quota', 'auth', 'timeout', 'bad_json', 'oversized'])
def test_riot_failures_and_token_never_leak(failure):
    def fake_open(request, timeout):
        assert timeout == 6
        assert request.headers['X-riot-token'] == 'test-secret'
        assert 'test-secret' not in request.full_url
        if failure == 'quota': raise HTTPError(request.full_url, 429, 'test-secret', {'Retry-After': '321'}, None)
        if failure == 'auth': raise HTTPError(request.full_url, 403, 'test-secret', {}, None)
        if failure == 'timeout': raise URLError('test-secret')
        if failure == 'bad_json': return BytesIO(b'test-secret')
        return BytesIO(b'x' * 8_000_001)
    client = RiotClient('test-secret', lambda: None, Clock())
    client.opener.open = fake_open
    with pytest.raises(RiotError) as error:
        client.get('/lol/match/v5/matches/BR1_1')
    assert 'test-secret' not in str(error.value)
    if failure == 'quota': assert error.value.retry_after == 321


def test_collector_uses_ladder_and_deduplicates_without_raw_storage(tmp_path):
    catalog_path = tmp_path / 'catalog.json'
    catalog_path.write_text(json.dumps(CATALOG), encoding='utf-8')
    match, timeline = documents(kills=[kill()])
    calls = []
    class Client:
        def get(self, path, platform=False):
            calls.append((path, platform))
            if '/entries/' in path: return [{'puuid': 'temporary-player'}]
            if '/ids?' in path: return ['BR1_1', 'BR1_1', 'NA1_3']
            if path.endswith('/timeline'): return timeline
            return match
    service = StatisticsService(tmp_path / 'stats.sqlite3', 'test-secret', catalog_path, Clock(), Client())
    assert service.collect(0) == 1
    assert service.collect(0) == 0
    assert sum(path.endswith('/timeline') for path, _ in calls) == 1
    assert calls[0][1] is True
    assert service.store.snapshot('Yone', 'Ahri', 'mid', CATALOG)['sample'] == 1


def test_web_without_key_and_cached_result_never_call_provider(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'legacy.sqlite3')})
    service = app.extensions['statistics']
    service.client.get = lambda *args, **kwargs: pytest.fail('Unexpected Riot request')
    client = app.test_client()
    query = '/api/statistics?champion=Yone&opponent=Ahri&lane=mid'
    assert client.get(query).json['state'] == 'unavailable'
    assert client.get('/api/statistics?champion=Yone&opponent=Yone&lane=mid').status_code == 400
    assert client.get('/api/statistics?champion=Yone&opponent=Aphelios&lane=mid').status_code == 503
    assert client.get(query + '&extra=1').status_code == 400
    seed(service.store)
    response = client.get(query)
    assert response.json['state'] == 'ready'
    assert 'Abates mais frequentes' in response.json['sides'][0]['tendency']
    html = client.get('/matchup?champion=Yone&opponent=Ahri&lane=mid').text
    assert 'Passivo' not in html and 'class="ability-coaching"' not in html
    assert 'ITENS NO INVENTÁRIO FINAL' in html
    assert 'test-secret' not in response.text
    backup = tmp_path / 'backup.sqlite3'
    runner = app.test_cli_runner()
    assert runner.invoke(args=['backup-db', '--statistics', str(backup)]).exit_code == 0
    assert StatisticsStore(backup).snapshot('Yone', 'Ahri', 'mid', CATALOG)['sample'] == 30
    assert runner.invoke(args=['backup-db', '--statistics', str(backup)]).exit_code != 0

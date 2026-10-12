"""Collect a small ranked sample, persist anonymous summaries and query matchups."""
import hashlib
import json
import logging
import math
import random
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

import click
from flask import current_app
from flask.cli import with_appcontext

from .riot import RiotClient, RiotError
from .classification import ROLES


POSITIONS = {'TOP': 'top', 'JUNGLE': 'jungle', 'MIDDLE': 'mid',
             'BOTTOM': 'adc', 'UTILITY': 'support'}
QUEUE = 420
WINDOW_MS = 900_000
MIN_SAMPLE = 30
VERSION = 1
TIERS = ('IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND',
         'MASTER', 'GRANDMASTER', 'CHALLENGER')


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def summarize_match(match, timeline, catalog):
    """No raw participants, names, PUUIDs or event locations are persisted."""
    info = match.get('info', {}) if isinstance(match, dict) else {}
    if (info.get('queueId') != QUEUE or info.get('mapId') != 11
            or info.get('gameEndedInEarlySurrender')
            or not isinstance(info.get('gameVersion'), str)
            or not info['gameVersion'].startswith('.'.join(catalog['patch'].split('.')[:2]) + '.')
            or not integer(info.get('gameDuration')) or info['gameDuration'] < 900):
        return None
    match_id = match.get('metadata', {}).get('matchId', '')
    if not isinstance(match_id, str) or not match_id.startswith('BR1_'):
        return None
    people = info.get('participants')
    frames = timeline.get('info', {}).get('frames') if isinstance(timeline, dict) else None
    if not isinstance(people, list) or len(people) != 10 or not isinstance(frames, list) or not frames:
        raise RiotError('invalid_response')
    if timeline.get('metadata', {}).get('matchId') != match_id:
        raise RiotError('invalid_response')
    if not all(isinstance(f, dict) and integer(f.get('timestamp')) and isinstance(f.get('events'), list)
               for f in frames) or max(f['timestamp'] for f in frames) < WINDOW_MS:
        raise RiotError('invalid_response')
    by_role = {}
    participants = set()
    for person in people:
        if not isinstance(person, dict) or not integer(person.get('participantId')):
            raise RiotError('invalid_response')
        pid = person['participantId']
        if pid not in range(1, 11) or pid in participants:
            raise RiotError('invalid_response')
        participants.add(pid)
        lane = POSITIONS.get(person.get('teamPosition'))
        team = person.get('teamId')
        champion = catalog['champions'].get(str(person.get('championId')))
        if not lane or team not in (100, 200) or not champion or not isinstance(person.get('win'), bool):
            continue
        key = (team, lane)
        if key in by_role:
            raise RiotError('invalid_response')
        by_role[key] = {'id': pid, 'champion': champion, 'win': person['win'],
                        'items': sorted({str(person.get(f'item{i}', 0)) for i in range(6)} & set(catalog['items']))}
    kills = []
    for frame in frames:
        for event in frame['events']:
            if not isinstance(event, dict):
                raise RiotError('invalid_response')
            if event.get('type') != 'CHAMPION_KILL':
                continue
            if (not integer(event.get('timestamp')) or not integer(event.get('killerId'))
                    or not integer(event.get('victimId'))
                    or event['victimId'] not in participants or event['killerId'] not in participants | {0}
                    or not isinstance(event.get('assistingParticipantIds', []), list)):
                raise RiotError('invalid_response')
            if 0 <= event['timestamp'] <= WINDOW_MS:
                kills.append(event)
    pairs = []
    for lane in POSITIONS.values():
        first, second = by_role.get((100, lane)), by_role.get((200, lane))
        if not first or not second or first['champion'] == second['champion']:
            continue
        pair = {'lane': lane, 'sides': [first, second]}
        for own, enemy in [(first, second), (second, first)]:
            direct = [e for e in kills if e['killerId'] == own['id'] and e['victimId'] == enemy['id']]
            own['kill'] = bool(direct)
            own['death'] = any(e['killerId'] == enemy['id'] and e['victimId'] == own['id'] for e in kills)
            own['unassisted'] = any(not e.get('assistingParticipantIds') for e in direct)
        for side in pair['sides']:
            del side['id']
        pairs.append(pair)
    started = info.get('gameStartTimestamp')
    if not integer(started) or started <= 0:
        raise RiotError('invalid_response')
    return {'match_hash': hashlib.sha256(match_id.encode()).hexdigest(),
            'played_at': started / 1000, 'patch': '.'.join(catalog['patch'].split('.')[:2]), 'pairs': pairs}


def tendency(rows):
    """Paired, discordant outcomes; do not infer aggression from event frequency."""
    positive = sum(r['kill'] and not r['death'] for r in rows)
    negative = sum(r['death'] and not r['kill'] for r in rows)
    count = positive + negative
    if not count:
        return 'Sem tendência clara'
    rate, z = positive / count, 1.96
    denominator = 1 + z * z / count
    center = (rate + z * z / (2 * count)) / denominator
    radius = z * math.sqrt(rate * (1 - rate) / count + z * z / (4 * count * count)) / denominator
    if center - radius > .5:
        return 'Abates mais frequentes'
    if center + radius < .5:
        return 'Mortes mais frequentes'
    return 'Sem tendência clara'


class StatisticsStore:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = str(path), clock
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.executescript('''
                CREATE TABLE IF NOT EXISTS sample_matches (
                    match_hash TEXT PRIMARY KEY, patch TEXT NOT NULL,
                    played_at REAL NOT NULL, collected_at REAL NOT NULL, summary TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS riot_requests (at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS collector (
                    id INTEGER PRIMARY KEY CHECK(id=1), cursor INTEGER NOT NULL DEFAULT 0,
                    lease_until REAL NOT NULL DEFAULT 0, next_collect REAL NOT NULL DEFAULT 0,
                    last_error TEXT, last_success REAL NOT NULL DEFAULT 0
                );
                INSERT OR IGNORE INTO collector(id) VALUES (1);
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def reserve(self):
        now = self.clock()
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('DELETE FROM riot_requests WHERE at <= ?', (now - 120,))
            rows = [r['at'] for r in con.execute('SELECT at FROM riot_requests ORDER BY at')]
            recent = [at for at in rows if at > now - 1]
            if len(rows) >= 90:
                raise RiotError('rate_limited', max(1, rows[0] + 120 - now))
            if len(recent) >= 18:
                raise RiotError('rate_limited', max(1, recent[0] + 1 - now))
            con.execute('INSERT INTO riot_requests VALUES (?)', (now,))

    def claim(self):
        now = self.clock()
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM collector WHERE id=1').fetchone()
            if row['lease_until'] > now or row['next_collect'] > now:
                return None
            cursor = row['cursor']
            con.execute('UPDATE collector SET lease_until=?, cursor=cursor+1, last_error=NULL WHERE id=1', (now + 240,))
            return cursor

    def finish(self, error=None):
        now = self.clock()
        with self.connection() as con:
            con.execute('UPDATE collector SET lease_until=0, next_collect=?, last_error=?, '
                        'last_success=CASE WHEN ? IS NULL THEN ? ELSE last_success END WHERE id=1',
                        (now + max(60, error.retry_after if error else 60),
                         error.code if error else None, error.code if error else None, now))

    def seen(self, match_id):
        digest = hashlib.sha256(match_id.encode()).hexdigest()
        with self.connection() as con:
            return con.execute('SELECT 1 FROM sample_matches WHERE match_hash=?', (digest,)).fetchone() is not None

    def add(self, summary):
        now = self.clock()
        # Retain at most 5000 summaries, for at most 30 days; never raw match payloads.
        with self.connection() as con:
            con.execute('INSERT OR IGNORE INTO sample_matches VALUES (?,?,?,?,?)',
                        (summary['match_hash'], summary['patch'], summary['played_at'], now,
                         json.dumps(summary['pairs'], separators=(',', ':'))))
            con.execute('DELETE FROM sample_matches WHERE collected_at < ?', (now - 30 * 86400,))
            con.execute('DELETE FROM sample_matches WHERE match_hash IN '
                        '(SELECT match_hash FROM sample_matches ORDER BY collected_at DESC LIMIT -1 OFFSET 5000)')

    def snapshot(self, own, enemy, lane, catalog):
        patch = '.'.join(catalog['patch'].split('.')[:2])
        selected, updated = [[], []], 0
        with self.connection() as con:
            records = con.execute('SELECT summary, collected_at FROM sample_matches WHERE patch=? '
                                  'AND collected_at >= ?', (patch, self.clock() - 30 * 86400)).fetchall()
            collector = dict(con.execute('SELECT * FROM collector WHERE id=1').fetchone())
        for record in records:
            for pair in json.loads(record['summary']):
                if pair['lane'] != lane:
                    continue
                sides = pair['sides']
                if {side['champion'] for side in sides} != {own, enemy}:
                    continue
                for i, champion in enumerate((own, enemy)):
                    selected[i].append(next(side for side in sides if side['champion'] == champion))
                updated = max(updated, record['collected_at'])
        sample = len(selected[0])
        result = {'sample': sample, 'minimum': MIN_SAMPLE, 'patch': patch, 'region': 'BR',
                  'lane': lane, 'lane_label': ROLES.get(lane, 'Selecionar lane'),
                  'queue': 'Ranked solo/duo', 'window_minutes': 15, 'updated_at': updated,
                  'state': 'ready' if sample >= MIN_SAMPLE else 'insufficient', 'sides': [],
                  'updating': collector['lease_until'] > self.clock(), 'version': VERSION,
                  'provider_issue': bool(collector['last_error']),
                  'next_collect': collector['next_collect']}
        for i, champion in enumerate((own, enemy)):
            rows = selected[i]
            items = []
            for key, item in catalog['items'].items():
                owners = [r for r in rows if key in r['items']]
                if len(owners) < 5:
                    continue
                items.append({'id': key, 'name': item['name'], 'count': len(owners),
                              'frequency': round(100 * len(owners) / sample, 1),
                              'win_rate': round(100 * sum(r['win'] for r in owners) / len(owners), 1)})
            items.sort(key=lambda item: (-item['count'], item['id']))
            result['sides'].append({'champion': champion,
                                   'tendency': tendency(rows) if sample >= MIN_SAMPLE else 'Amostra insuficiente',
                                   'kill_pct': round(100 * sum(r['kill'] for r in rows) / sample, 1) if sample else None,
                                   'death_pct': round(100 * sum(r['death'] for r in rows) / sample, 1) if sample else None,
                                   'unassisted_pct': round(100 * sum(r['unassisted'] for r in rows) / sample, 1) if sample else None,
                                   'items': items[:3] if sample >= MIN_SAMPLE else []})
        return result


class StatisticsService:
    def __init__(self, path, key, catalog_path=None, clock=time.time, client=None):
        self.clock, self.key = clock, key
        self.catalog = json.loads((catalog_path or Path(__file__).parent / 'data/statistics_catalog.json').read_text(encoding='utf-8'))
        self.store = StatisticsStore(path, clock)
        self.client = client or RiotClient(key, self.store.reserve, clock)

    def collect(self, cursor, max_matches=8):
        """One bounded job. PUUID is transient, taken from the public ranked ladder."""
        tier = TIERS[cursor % len(TIERS)]
        page = 1 + (cursor // len(TIERS)) % 3
        if tier in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
            response = self.client.get(f'/lol/league/v4/{tier.lower()}leagues/by-queue/RANKED_SOLO_5x5', platform=True)
            entries = response.get('entries') if isinstance(response, dict) else None
        else:
            entries = self.client.get(f'/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/IV?page={page}', platform=True)
        if not isinstance(entries, list):
            raise RiotError('invalid_response')
        candidates = [e['puuid'] for e in entries if isinstance(e, dict) and isinstance(e.get('puuid'), str) and e['puuid']]
        if not candidates:
            if entries:
                raise RiotError('invalid_response')
            return 0
        puuid = random.SystemRandom().choice(candidates)
        ids = self.client.get('/lol/match/v5/matches/by-puuid/' + quote(puuid, safe='') + '/ids?queue=420&count=20')
        if not isinstance(ids, list) or any(not isinstance(key, str) for key in ids):
            raise RiotError('invalid_response')
        saved, inspected = 0, 0
        for match_id in dict.fromkeys(ids):
            if inspected >= max_matches:
                break
            if not match_id.startswith('BR1_') or not match_id[4:].isdigit() or self.store.seen(match_id):
                continue
            inspected += 1
            try:
                match = self.client.get('/lol/match/v5/matches/' + match_id)
                if not isinstance(match, dict):
                    raise RiotError('invalid_response')
                if match.get('metadata', {}).get('matchId') != match_id:
                    raise RiotError('invalid_response')
                info = match.get('info', {})
                if (info.get('queueId') != QUEUE or info.get('mapId') != 11
                        or info.get('gameEndedInEarlySurrender') or not integer(info.get('gameDuration'))
                        or info['gameDuration'] < 900 or not isinstance(info.get('gameVersion'), str)
                        or not info['gameVersion'].startswith('.'.join(self.catalog['patch'].split('.')[:2]) + '.')):
                    continue
                timeline = self.client.get('/lol/match/v5/matches/' + match_id + '/timeline')
                summary = summarize_match(match, timeline, self.catalog)
                if summary:
                    self.store.add(summary)
                    saved += 1
            except RiotError as error:
                if error.code == 'not_found':
                    continue
                raise
        return saved

    def run(self, cursor):
        error = None
        try:
            self.collect(cursor)
        except RiotError as caught:
            error = caught
        except (ValueError, TypeError, KeyError, AttributeError, sqlite3.Error):
            error = RiotError('collection_failed')
        finally:
            self.store.finish(error)
            if error:
                logging.getLogger(__name__).warning('Riot collection stopped (%s).', error.code)

    def request(self, own, enemy, lane, schedule=True):
        result = self.store.snapshot(own, enemy, lane, self.catalog)
        if lane == 'general':
            result['state'] = 'choose_lane'
        elif self.key and schedule:
            fresh = result['state'] == 'ready' and result['updated_at'] > self.clock() - 6 * 3600
            cursor = None if fresh else self.store.claim()
            if cursor is not None:
                result['updating'] = True
                threading.Thread(target=self.run, args=(cursor,), daemon=True).start()
            if result['updating'] and result['state'] != 'ready':
                result['state'] = 'loading'
            elif result['provider_issue'] and result['state'] != 'ready':
                result['state'] = 'unavailable'
        elif not self.key and not result['sample']:
            result['state'] = 'unavailable'
        return result


@click.command('collect-stats')
@with_appcontext
def collect_stats():
    """Collect ranked match summaries, respecting persistent quotas and cooldowns."""
    service = current_app.extensions['statistics']
    if not service.key:
        raise click.ClickException('Configure RIOT_API_KEY somente no servidor; não cole a chave no chat.')
    cursor = service.store.claim()
    if cursor is None:
        click.echo('Coleta aguardando intervalo/cota; dados já salvos foram preservados.')
        return
    error = None
    try:
        count = service.collect(cursor)
        click.echo(f'{count} partidas elegíveis processadas; agregados persistidos, sem dados de jogadores.')
    except RiotError as caught:
        error = caught
        raise click.ClickException('Coleta interrompida: ' + caught.code) from None
    finally:
        service.store.finish(error)

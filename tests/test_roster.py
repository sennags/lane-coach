import json
import pytest
from pathlib import Path

from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase, MAINTENANCE_CHAMPIONS


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_covers_every_official_champion_and_image():
    manifest = json.loads((ROOT / 'lane_coach/data/roster.json').read_text())
    base = KnowledgeBase()
    assert set(base.champions) == set(manifest['champion_ids'])
    for key, champion in base.champions.items():
        assert champion['source']['patch'] == manifest['patch']
        assert {fact['ability'] for fact in champion['facts']} == {'P', 'Q', 'W', 'E', 'R'}
        assert all(fact['description'] and fact['name'] for fact in champion['facts'])
        image = ROOT / 'lane_coach/static/champions' / f'{key}.jpg'
        assert image.read_bytes().startswith(b'\xff\xd8'), key
        assert champion['profile']['basis'] in ('champion_specific', 'class_based')


def test_ability_icons_cover_roster_with_official_sources():
    base = KnowledgeBase()
    patch = json.loads((ROOT / 'lane_coach/data/roster.json').read_text())['patch']
    directory = ROOT / 'lane_coach/static/abilities' / patch
    sources = json.loads((directory / 'sources.json').read_text())
    assert set(sources) == set(base.champions)
    for champion in base.champions:
        assert set(sources[champion]) == set('PQWER')
        for ability, url in sources[champion].items():
            group = 'passive' if ability == 'P' else 'spell'
            assert url.startswith(f'https://ddragon.leagueoflegends.com/cdn/{patch}/img/{group}/')
            assert (directory / champion / f'{ability}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert sources['Yone']['P'].endswith('/YonePassive.png')
    assert sources['Ahri']['Q'].endswith('/AhriQ.png')


def test_catalog_requests_respect_maintenance_without_network(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})
    client = app.test_client()
    ids = list(app.extensions['knowledge'].champions)
    for index, own in enumerate(ids):
        enemy = ids[(index + 1) % len(ids)]
        response = client.get('/matchup', query_string={'champion': own, 'opponent': enemy, 'lane': 'general'})
        maintenance = own in MAINTENANCE_CHAMPIONS or enemy in MAINTENANCE_CHAMPIONS
        assert response.status_code == (503 if maintenance else 200), own
        if maintenance:
            assert 'Campeão em manutenção' in response.text
            assert 'class="champion-profile ' not in response.text
        else:
            assert response.text.count('class="champion-profile ') == 2
        assert 'Set-Cookie' not in response.headers


def test_initial_profiles_and_missing_official_advice_are_honest(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})
    base = app.extensions['knowledge']
    for key in ('Yone', 'Ahri', 'Yasuo', 'Zed'):
        assert base.champions[key]['profile']['basis'] == 'champion_specific'
        assert len(base.champions[key]['tips']) == 5
    response = app.test_client().get('/matchup?champion=Yuumi&opponent=Singed&lane=general')
    assert response.status_code == 200
    assert 'Perfil inicial por classe' not in response.text
    assert '5 decisões para praticar' not in response.text
    assert base.champions['Yuumi']['profile']['status'] == 'editorial_unreviewed'
    assert response.text.count('class="ability-coaching"') == 10


def test_maintenance_blocks_both_perspectives_and_preserves_catalog(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'maintenance.sqlite3')})
    base = app.extensions['knowledge']
    client = app.test_client()
    for champion in MAINTENANCE_CHAMPIONS:
        assert champion in base.champions
        for own, enemy in [(champion, 'Yone'), ('Yone', champion)]:
            response = client.get('/matchup', query_string={'champion': own, 'opponent': enemy, 'lane': 'mid'})
            assert response.status_code == 503
            assert 'Campeão em manutenção' in response.text
            assert 'class="champion-profile ' not in response.text
            with pytest.raises(ValueError, match='maintenance'):
                base.context(own, enemy)

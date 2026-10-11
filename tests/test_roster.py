import json
from pathlib import Path

from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase


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


def test_every_champion_can_be_requested_without_network(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})
    client = app.test_client()
    ids = list(app.extensions['knowledge'].champions)
    for index, own in enumerate(ids):
        enemy = ids[(index + 1) % len(ids)]
        response = client.get('/matchup', query_string={'champion': own, 'opponent': enemy, 'lane': 'general'})
        assert response.status_code == 200, own
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
    assert 'Perfil inicial por classe' in response.text
    assert '5 decisões para praticar' not in response.text
    assert 'revisão especializada pendente' in response.text

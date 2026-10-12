import itertools
import json

import pytest

from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase


@pytest.fixture
def knowledge():
    return KnowledgeBase()


@pytest.mark.parametrize('own,enemy', itertools.permutations(['Yone', 'Ahri', 'Yasuo', 'Zed'], 2))
def test_composes_every_direction(knowledge, own, enemy):
    guide = knowledge.guide(own, enemy)
    assert len(guide['sections']) == 5
    assert [s['champion'] for s in guide['sections']] == [enemy] * 3 + [own] * 2
    assert all(s['evidence'] and s['exception'] for s in guide['sections'])
    assert guide['status'] == 'demo'
    assert [profile['id'] for profile in guide['profiles']] == [own, enemy]
    assert all(set(profile['profile']['phases']) == {'lane', 'mid', 'late'}
               for profile in guide['profiles'])
    assert knowledge.context(own, enemy)['own']['id'] == own


def test_context_is_isolated_and_version_changes(knowledge, tmp_path):
    context = knowledge.context('Yone', 'Ahri')
    context['own']['tips'][0]['action'] = 'changed'
    assert knowledge.context('Yone', 'Ahri')['own']['tips'][0]['action'] != 'changed'
    for key, value in knowledge.champions.items():
        (tmp_path / f'{key}.json').write_text(json.dumps(value), encoding='utf-8')
    assert KnowledgeBase(tmp_path).version == knowledge.version
    (tmp_path / 'Yone.json').write_text(json.dumps(context['own']), encoding='utf-8')
    assert KnowledgeBase(tmp_path).version != knowledge.version


def test_unknown_evidence_blocks_loading(knowledge, tmp_path):
    champion = knowledge.context('Yone', 'Ahri')['own']
    champion['tips'][0]['evidence_ids'] = ['invented']
    (tmp_path / 'Yone.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)


@pytest.mark.parametrize('failure', ['missing_phase', 'empty_plan', 'empty_weaknesses', 'false_review'])
def test_incomplete_profiles_are_rejected(knowledge, tmp_path, failure):
    champion = knowledge.context('Yone', 'Ahri')['own']
    profile = champion['profile']
    if failure == 'missing_phase': del profile['phases']['late']
    if failure == 'empty_plan': profile['phases']['lane']['plan'] = ' '
    if failure == 'empty_weaknesses': profile['weaknesses'] = []
    if failure == 'false_review': profile['status'] = 'reviewed'
    (tmp_path / 'Yone.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)


def test_profile_output_preserves_perspective_and_escapes_content(knowledge, tmp_path):
    for key, champion in knowledge.champions.items():
        data = json.loads(json.dumps(champion))
        if key == 'Yone': data['facts'][0]['name'] = '<script>alert(1)</script>'
        (tmp_path / f'{key}.json').write_text(json.dumps(data), encoding='utf-8')
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3'),
                      'KNOWLEDGE_PATH': str(tmp_path)})
    response = app.test_client().get('/matchup?champion=Ahri&opponent=Yone&lane=mid')
    assert response.status_code == 200
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in response.text
    assert 'aria-label="Categorias de Ahri"' in response.text
    assert 'aria-label="Categorias de Yone"' in response.text
    assert 'data-phase=' not in response.text

import json

import pytest

from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase


def test_direct_plan_is_independent_of_opponent_and_lane():
    base = KnowledgeBase()
    first = base.guide('Yone', 'Ahri', 'mid')['profiles'][0]['direct']
    other = base.guide('Yone', 'Zed', 'top')['profiles'][0]['direct']
    assert first == other
    reverse = base.guide('Ahri', 'Yone')['profiles'][1]['direct']
    for key in first:
        assert reverse[key]['resource'] == first[key]['resource']
        assert reverse[key]['caution'] == first[key]['caution']
        assert reverse[key]['action'] == base.champions['Yone']['profile']['phases'][key]['against']
    first['lane']['action'] = 'mutated'
    assert base.guide('Yone', 'Ahri')['profiles'][0]['direct']['lane']['action'] != 'mutated'


def test_two_sections_with_official_fallback(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'direct.sqlite3')})
    client = app.test_client()
    specific = client.get('/matchup?champion=Akshan&opponent=Aatrox&lane=top').text
    assert 'traits-pair' not in specific
    assert 'micro-library' not in specific
    assert 'class="direct-plan"' not in specific
    assert specific.count('class="classification-facts"') == 2
    assert specific.count('class="ability-coaching"') == 0
    assert 'Descrição oficial' not in specific
    fallback = client.get('/matchup?champion=Yuumi&opponent=Singed&lane=support').text
    assert 'Perfil inicial por classe' not in fallback
    assert 'Notas de uso e limite ainda não preparadas' not in fallback
    assert fallback.count('class="ability-coaching"') == 0
    assert 'class="profile-source"' not in fallback


@pytest.mark.parametrize('field,value', [('resource', ''), ('caution', 42), ('coaching', {'use': 'only'})])
def test_invalid_editorial_fields_are_rejected(tmp_path, field, value):
    champion = KnowledgeBase().champions['Yone']
    if field == 'coaching':
        champion['facts'][0][field] = value
    else:
        champion['profile']['phases']['lane'][field] = value
    (tmp_path / 'Yone.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)

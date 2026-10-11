import json
from pathlib import Path

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
    assert specific.count('class="direct-plan"') == 6
    assert specific.count('class="ability-coaching"') == 10
    assert 'Descrição oficial' not in specific
    fallback = client.get('/matchup?champion=Yuumi&opponent=Singed&lane=support').text
    assert 'Perfil inicial por classe' not in fallback
    assert 'Notas de uso e limite ainda não preparadas' not in fallback
    assert fallback.count('class="ability-coaching"') == 10
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


def test_import_preserves_notes_only_for_unchanged_mechanics(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    from import_roster import make_record
    base = KnowledgeBase().champions['Aatrox']
    facts = {f['ability']: f for f in base['facts']}
    raw = {'id': base['id'], 'name': base['name'], 'title': base['title'], 'tags': base['tags'],
           'spells': [{'name': facts[k]['name'], 'description': facts[k]['description']} for k in 'QWER'],
           'passive': {'name': facts['P']['name'], 'description': facts['P']['description']}}
    templates = json.loads((Path(__file__).resolve().parents[1] / 'lane_coach/data/profile_templates.json').read_text(encoding='utf-8'))
    imported = make_record(raw, base['source']['patch'], templates, base)
    assert imported['profile'] == base['profile']
    assert all('coaching' in f for f in imported['facts'])
    raw['spells'][0]['description'] = 'Changed mechanical snapshot'
    changed = make_record(raw, base['source']['patch'], templates, base)
    assert 'coaching' not in changed['facts'][0]
    assert 'coaching' in changed['facts'][1]
    new_patch = make_record(raw, '99.1.1', templates, base)
    assert all('coaching' not in fact for fact in new_patch['facts'])

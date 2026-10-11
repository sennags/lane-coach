import json
from copy import deepcopy

import pytest

from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase


def test_roster_categories_are_editorial_and_independent():
    base = KnowledgeBase()
    assert len(base.champions) == 173
    for champion in base.champions.values():
        category = champion['classification']
        assert category['status'] == 'editorial_unreviewed'
        assert category['reviewed_at'] is None
        assert category['content_patch'] == champion['source']['patch']
        assert category['sources'] == [champion['source']['url']]
    first = base.guide('Yone', 'Ahri', 'mid')['profiles'][0]['classification']
    other = base.guide('Yone', 'Zed', 'top')['profiles'][0]['classification']
    assert first == other
    first['behavior']['tendency'] = 'aggressive'
    assert base.champions['Yone']['classification']['behavior']['tendency'] == 'passive'


@pytest.mark.parametrize('field,value', [
    ('primary_role', 'general'), ('class', 'Support'), ('damage', 'AD'),
    ('behavior', {'tendency': 'aggressive', 'context': 'jungle'}),
    ('behavior', {'tendency': [], 'context': 'lane', 'condition': 'x'}),
    ('status', 'reviewed'), ('sources', []),
])
def test_invalid_or_falsely_reviewed_categories_block_loading(tmp_path, field, value):
    champion = deepcopy(KnowledgeBase().champions['Ahri'])
    champion['classification'][field] = value
    (tmp_path / 'Ahri.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)


def test_categories_replace_phase_plans_and_jungle_has_own_context(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})
    client = app.test_client()
    html = client.get('/matchup?champion=LeeSin&opponent=Evelynn&lane=mid').text
    assert html.count('class="classification-facts"') == 2
    assert html.count('class="jungle-behavior"') == 2
    assert '<dt>LANE</dt>' not in html
    assert '<dt>JUNGLE</dt>' in html
    assert 'INVASÃO' in html and 'GANK' in html and 'RISCO' in html
    assert 'data-phase-button' not in html and 'data-phase=' not in html
    assert 'não é um contador da partida' not in html
    assert html.count('class="ability-coaching"') == 10
    reverse = client.get('/matchup?champion=Evelynn&opponent=LeeSin&lane=jungle').text
    assert reverse.index('Categorias de Evelynn') < reverse.index('Categorias de Lee Sin')


def test_import_preserves_categories_without_claiming_new_patch_review(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    from import_roster import make_record
    champion = KnowledgeBase().champions['Ahri']
    facts = {fact['ability']: fact for fact in champion['facts']}
    raw = {'id': champion['id'], 'name': champion['name'], 'title': champion['title'],
           'tags': champion['tags'], 'passive': facts['P'],
           'spells': [facts[key] for key in 'QWER']}
    templates = json.loads((Path(__file__).resolve().parents[1] /
                            'lane_coach/data/profile_templates.json').read_text(encoding='utf-8'))
    imported = make_record(raw, '99.1.1', templates, champion)
    assert imported['classification'] == champion['classification']
    assert imported['classification']['content_patch'] != imported['source']['patch']
    imported['classification']['primary_role'] = 'top'
    assert champion['classification']['primary_role'] == 'mid'

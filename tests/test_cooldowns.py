import json
from pathlib import Path

import pytest

from lane_coach.cooldowns import spell_cooldowns, cooldown_note, annotate_cooldown
from lane_coach.knowledge import KnowledgeBase


@pytest.mark.parametrize('values', [[], [-1], [True], ['12'], [float('nan')], [float('inf')]])
def test_invalid_cooldowns_are_not_presented(values):
    assert spell_cooldowns({'cooldown': values, 'maxrank': len(values)}) is None


def test_preserves_rank_order_fractions_and_zero():
    assert spell_cooldowns({'cooldown': [14, 13.5, 0], 'maxrank': 3}) == [14, 13.5, 0]
    assert spell_cooldowns({'cooldown': [14, 13], 'maxrank': 5}) is None
    assert spell_cooldowns({}) is None


def test_roster_cooldowns_match_official_source_shape():
    base = KnowledgeBase()
    for champion in base.champions.values():
        for fact in champion['facts']:
            if fact['ability'] == 'P':
                assert fact['cooldown'] is None
            else:
                assert isinstance(fact['cooldown'], list) and fact['cooldown']


def test_invalid_stored_cooldown_is_rejected(tmp_path):
    champion = KnowledgeBase().champions['Akshan']
    champion['facts'][0]['cooldown'] = [-1]
    (tmp_path / 'Akshan.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError, match='cooldown'):
        KnowledgeBase(tmp_path)


def test_scaling_note_requires_explicit_cooldown_relationship():
    base = {'cooldown': [14] * 5, 'maxrank': 5}
    assert cooldown_note({**base, 'description': 'O Tempo de Recarga escala com Velocidade de Ataque.'})
    assert cooldown_note({**base, 'description': 'O dano escala com Velocidade de Ataque.'}) is None
    assert cooldown_note({**base, 'description': 'Concede Velocidade de Ataque e de Movimento.'}) is None
    assert cooldown_note({**base, 'cooldown': [14, 13, 12, 11, 10], 'description': 'O Tempo de Recarga escala com Velocidade de Ataque.'}) is None


def test_special_rules_require_matching_patch_and_base_values():
    spell = {'cooldown': [4] * 5, 'maxrank': 5, 'description': 'Dano em linha.'}
    fact = {'ability': 'Q', 'cooldown': [4] * 5}
    annotate_cooldown(fact, 'Yone', '16.20.1', spell)
    assert '1,33 s' in fact['cooldown_note']
    assert fact['cooldown_source']['url'].startswith('https://')
    annotate_cooldown(fact, 'Yone', '16.21.1', spell)
    assert 'cooldown_note' not in fact and 'cooldown_source' not in fact
    fact['cooldown'] = [5] * 5
    annotate_cooldown(fact, 'Yone', '16.20.1', spell)
    assert 'cooldown_note' not in fact


def test_zeri_and_belveth_do_not_present_catalog_timer_as_only_cooldown(tmp_path):
    from lane_coach import create_app
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'special.sqlite3')})
    html = app.test_client().get('/matchup?champion=Zeri&opponent=Belveth&lane=mid').text
    assert 'Intervalo entre disparos: 1 ÷ Velocidade de Ataque total' in html
    assert 'Cada direção tem recarga própria' in html
    assert 'Intervalo entre usos: 4 / 3,25 / 2,5 / 1,75 / 1 s' in html
    assert 'LoL Wiki · disparos do Q' not in html
    assert 'wiki.leagueoflegends.com' not in html

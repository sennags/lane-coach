import json
from pathlib import Path

import pytest

from lane_coach.cooldowns import spell_cooldowns, cooldown_note
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

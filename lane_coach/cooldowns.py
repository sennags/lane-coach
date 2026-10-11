"""Read base spell cooldowns without inferring timers from description text."""
import math
import re
import json
from pathlib import Path

RULES = json.loads((Path(__file__).parent / 'data/cooldown_rules.json').read_text(encoding='utf-8'))


def valid_cooldowns(values):
    return isinstance(values, list) and bool(values) and all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and value >= 0 for value in values
    )


def spell_cooldowns(spell):
    values = spell.get('cooldown')
    if not valid_cooldowns(values) or len(values) != spell.get('maxrank'):
        return None
    return [int(value) if value == int(value) else value for value in values]


def cooldown_note(spell):
    """Keep only explicit cooldown scaling from the official description."""
    values = spell_cooldowns(spell)
    if values is None or len(set(values)) != 1:
        return None
    description = re.sub(r'<[^>]+>', ' ', spell.get('description', '')).casefold()
    if 'tempo de recarga' in description and 'escal' in description and 'velocidade de ataque' in description:
        return 'Recarga escala com Velocidade de Ataque.'
    if 'tempo de recarga' in description and 'acúmulos de poder maligno fenomenal' in description:
        return 'Acúmulos de Poder Maligno Fenomenal reduzem a recarga.'
    return None


def annotate_cooldown(fact, champion_id, patch, spell):
    """Use sourced special mechanics only for the matching recorded snapshot."""
    for field in ('cooldown_note', 'cooldown_label', 'cooldown_source'):
        fact.pop(field, None)
    note = cooldown_note(spell)
    if note:
        fact['cooldown_note'] = note
    rule = RULES['rules'].get(f"{champion_id}.{fact['ability']}")
    if (rule is None or patch != RULES['patch']
            or fact.get('cooldown') != rule['expected_base']):
        return
    fact['cooldown_note'] = rule['note']
    if 'label' in rule:
        fact['cooldown_label'] = rule['label']
    fact['cooldown_source'] = {
        'url': rule['source_url'], 'label': rule['source_label'],
        'accessed_at': RULES['accessed_at'],
    }

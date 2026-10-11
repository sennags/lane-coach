"""Read base spell cooldowns without inferring timers from description text."""
import math
import re


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

"""Read base spell cooldowns without inferring timers from description text."""
import math


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

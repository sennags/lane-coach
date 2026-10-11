"""Validate independent, editorial champion categories."""
from datetime import date


ROLES = {'top': 'Top', 'jungle': 'Jungle', 'mid': 'Mid', 'adc': 'ADC', 'support': 'Support'}
CLASSES = frozenset({'Controller', 'Fighter', 'Mage', 'Marksman', 'Slayer', 'Tank', 'Specialist'})
DAMAGE = {'physical': 'Físico', 'magic': 'Mágico', 'mixed': 'Misto'}
TENDENCIES = {'aggressive': 'Agressivo', 'passive': 'Passivo'}


def validate_classification(value):
    if not isinstance(value, dict):
        raise ValueError('Missing champion classification')
    for field, allowed in [('primary_role', ROLES), ('class', CLASSES),
                           ('damage', DAMAGE)]:
        if not isinstance(value.get(field), str) or value[field] not in allowed:
            raise ValueError('Invalid champion classification: ' + field)
    behavior = value.get('behavior')
    if (not isinstance(behavior, dict) or not isinstance(behavior.get('tendency'), str)
            or behavior['tendency'] not in TENDENCIES):
        raise ValueError('Invalid champion behavior')
    context = 'jungle' if value['primary_role'] == 'jungle' else 'lane'
    fields = {'tendency', 'context', 'invade', 'gank', 'invasion_risk'} if context == 'jungle' else {'tendency', 'context', 'condition'}
    if set(behavior) != fields or behavior['context'] != context or any(
        not isinstance(text, str) or not text.strip() for text in behavior.values()
    ):
        raise ValueError('Incomplete champion behavior')
    if value.get('status') not in ('editorial_unreviewed', 'reviewed'):
        raise ValueError('Invalid classification review status')
    if value['status'] == 'reviewed' and not value.get('reviewed_at'):
        raise ValueError('Reviewed classification needs review date')
    for field in ('authored_at', 'content_patch', 'basis'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError('Missing classification provenance')
    date.fromisoformat(value['authored_at'])
    if value.get('reviewed_at'):
        date.fromisoformat(value['reviewed_at'])
    sources = value.get('sources')
    if not isinstance(sources, list) or not sources or any(
        not isinstance(source, str) or not source.startswith('https://') for source in sources
    ):
        raise ValueError('Missing classification sources')

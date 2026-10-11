"""Compose local coaching context from independent champion files."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from .cooldowns import valid_cooldowns
from .classification import validate_classification


LANES = {'general': 'Selecionar lane', 'top': 'Top', 'jungle': 'Jungle', 'mid': 'Mid', 'adc': 'ADC', 'support': 'Support'}


MAINTENANCE_CHAMPIONS = frozenset({'Aphelios', 'Hwei'})


class KnowledgeBase:
    def __init__(self, directory=None):
        directory = directory or Path(__file__).parent / 'data' / 'champions'
        self.champions = {}
        for path in sorted(Path(directory).glob('*.json')):
            champion = json.loads(path.read_text(encoding='utf-8'))
            validate_classification(champion.get('classification'))
            if champion['id'] in self.champions:
                raise ValueError('Duplicate champion')
            facts = {fact['id'] for fact in champion['facts']}
            if len(facts) != len(champion['facts']):
                raise ValueError('Duplicate fact')
            profile = champion.get('profile')
            if not isinstance(profile, dict):
                raise ValueError('Missing champion profile')
            if not isinstance(profile.get('identity'), str) or not profile['identity'].strip():
                raise ValueError('Invalid champion identity')
            for field in ('strengths', 'weaknesses'):
                values = profile.get(field)
                if not isinstance(values, list) or not values or any(
                    not isinstance(value, str) or not value.strip() for value in values
                ):
                    raise ValueError('Invalid champion strengths or weaknesses')
            phases = profile.get('phases')
            if not isinstance(phases, dict) or set(phases) != {'lane', 'mid', 'late'}:
                raise ValueError('Missing game phase')
            for phase in phases.values():
                if not isinstance(phase, dict) or any(
                    not isinstance(phase.get(key), str) or not phase[key].strip()
                    for key in ('typical', 'plan', 'against')
                ):
                    raise ValueError('Incomplete game phase')
                for key in ('resource', 'caution'):
                    if key in phase and (not isinstance(phase[key], str) or not phase[key].strip()):
                        raise ValueError('Invalid direct plan')
            for fact in champion['facts']:
                if fact.get('cooldown') is not None and not valid_cooldowns(fact['cooldown']):
                    raise ValueError('Invalid cooldown data')
                if 'cooldown_note' in fact and (not isinstance(fact['cooldown_note'], str) or not fact['cooldown_note'].strip()):
                    raise ValueError('Invalid cooldown note')
                if 'cooldown_label' in fact and (not isinstance(fact['cooldown_label'], str) or not fact['cooldown_label'].strip()):
                    raise ValueError('Invalid cooldown label')
                if 'cooldown_source' in fact:
                    source = fact['cooldown_source']
                    if (not isinstance(source, dict) or set(source) != {'url', 'label', 'accessed_at'}
                            or any(not isinstance(v, str) or not v.strip() for v in source.values())
                            or not source['url'].startswith('https://')):
                        raise ValueError('Invalid cooldown source')
                if 'coaching' in fact and (
                    not isinstance(fact['coaching'], dict)
                    or set(fact['coaching']) != {'use', 'limit'}
                    or any(not isinstance(value, str) or not value.strip()
                           for value in fact['coaching'].values())
                ):
                    raise ValueError('Invalid ability coaching')
            if profile.get('status') not in ('editorial_unreviewed', 'reviewed'):
                raise ValueError('Invalid profile review status')
            if profile['status'] == 'reviewed' and not profile.get('reviewed_at'):
                raise ValueError('Reviewed profile needs review date')
            for tip in champion['tips']:
                if tip['perspective'] not in ('own', 'against') or not tip['evidence_ids']:
                    raise ValueError('Invalid tip')
                if not set(tip['evidence_ids']) <= facts:
                    raise ValueError('Unknown evidence')
                for key in ('title', 'situation', 'action', 'reason', 'exception'):
                    if not isinstance(tip[key], str) or not tip[key].strip():
                        raise ValueError('Invalid tip text')
            self.champions[champion['id']] = champion
        if not self.champions:
            raise ValueError('Empty knowledge base')
        serialized = json.dumps(self.champions, sort_keys=True, ensure_ascii=False)
        self.version = hashlib.sha256(serialized.encode()).hexdigest()[:12]

    def context(self, own, enemy, lane='mid'):
        if own == enemy or lane not in LANES:
            raise ValueError('Unsupported matchup')
        if own not in self.champions or enemy not in self.champions:
            raise ValueError('Unknown champion')
        if own in MAINTENANCE_CHAMPIONS or enemy in MAINTENANCE_CHAMPIONS:
            raise ValueError('Champion under maintenance')
        return deepcopy({
            'version': self.version, 'lane': lane,
            'own': self.champions[own], 'enemy': self.champions[enemy],
            'limitations': [
                'A partida não é observada: vida, nível e cooldowns são desconhecidos.',
                'As dicas são interpretações editoriais, sem revisão especializada.',
                'Mecânicas isoladas não comprovam interações entre habilidades.',
            ],
        })

    def guide(self, own, enemy, lane='mid'):
        context = self.context(own, enemy, lane)
        sections = []
        for side, perspective, limit in [('enemy', 'against', 3), ('own', 'own', 2)]:
            champion = context[side]
            facts = {fact['id']: fact for fact in champion['facts']}
            tips = [tip for tip in champion['tips'] if tip['perspective'] == perspective][:limit]
            for tip in tips:
                sections.append({**tip, 'champion': champion['name'],
                                 'evidence': [facts[key] for key in tip['evidence_ids']],
                                 'source': champion['source']})
        profiles = []
        for side, key in [('ally', 'own'), ('enemy', 'enemy')]:
            champion = context[key]
            profile = champion['profile']
            direct = {}
            for phase_key, phase in profile['phases'].items():
                fallback_caution = (
                    ' '.join(profile['weaknesses']) if phase_key == 'lane' else
                    'Pressão lateral sem visão pode isolar o campeão e atrasar sua chegada ao objetivo.'
                    if phase_key == 'mid' else
                    'Uma saída pela lateral sem avaliar o objetivo e a posição dos times pode custar uma luta decisiva.'
                )
                action = phase['plan' if side == 'ally' else 'against']
                if profile.get('basis') == 'class_based' and side == 'enemy' and phase_key != 'lane':
                    action = 'Acompanhe a pressão lateral e a chegada desse campeão ao objetivo. ' + action
                direct[phase_key] = {
                    'resource': phase.get('resource', phase['typical']),
                    'action': action,
                    'caution': phase.get('caution', fallback_caution),
                }
            profiles.append({'side': side, **champion, 'direct': direct})
        return {
            'title': 'Conheça os dois lados, em cada fase.',
            'summary': 'Pontos fortes, vulnerabilidades e planos de jogo de cada campeão. '
                       'Use os perfis para orientar suas decisões; a vantagem específica entre os dois ainda não é calculada.',
            'profiles': profiles,
            'status': 'demo', 'revision': self.version, 'sections': sections,
            'patch': 'Não validado', 'reviewed_at': None,
        }

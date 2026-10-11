"""Compose local coaching context from independent champion files."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path


class KnowledgeBase:
    def __init__(self, directory=None):
        directory = directory or Path(__file__).parent / 'data' / 'champions'
        self.champions = {}
        for path in sorted(Path(directory).glob('*.json')):
            champion = json.loads(path.read_text(encoding='utf-8'))
            if champion['id'] in self.champions:
                raise ValueError('Duplicate champion')
            facts = {fact['id'] for fact in champion['facts']}
            if len(facts) != len(champion['facts']):
                raise ValueError('Duplicate fact')
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
        if own == enemy or lane != 'mid':
            raise ValueError('Unsupported matchup')
        if own not in self.champions or enemy not in self.champions:
            raise ValueError('Unknown champion')
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
        return {
            'title': 'Observe o sinal. Escolha sua resposta.',
            'summary': f'Três ameaças de {enemy} e duas ferramentas de {own}. '
                       'As dicas são reutilizáveis por campeão; não representam uma interação específica validada.',
            'status': 'demo', 'revision': self.version, 'sections': sections,
            'patch': 'Não validado', 'reviewed_at': None,
        }

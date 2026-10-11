"""Import the official roster. Preserve existing authored profiles and micro tips."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from html import unescape
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lane_coach.knowledge import KnowledgeBase


def fetch_json(url):
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def plain(value):
    return ' '.join(unescape(re.sub(r'<[^>]*>', ' ', value)).split())


def make_record(data, patch, templates, existing=None):
    key = data['id']
    spells = dict(zip('QWER', data['spells']))
    spells['P'] = data['passive']
    facts = [{'id': f'{key}.{ability}', 'ability': ability, 'name': spell['name'],
              'description': plain(spell['description'])} for ability, spell in spells.items()]
    template = deepcopy(templates[data['tags'][0]])
    profile = {name: template[name] for name in ('identity', 'weaknesses', 'phases')}
    profile.update(
        strengths=[f"{fact['name']}: {fact['description']}" for fact in facts if fact['ability'] in ('Q', 'R')],
        basis='class_based', class_label=template['label'],
        status='editorial_unreviewed', reviewed_at=None,
    )
    tips = []
    if existing:
        tips = existing['tips']
        if existing['profile'].get('basis') != 'class_based':
            profile = existing['profile']
            profile.setdefault('basis', 'champion_specific')
    return {
        'id': key, 'name': data['name'], 'title': data['title'], 'tags': data['tags'],
        'source': {'url': f'https://ddragon.leagueoflegends.com/cdn/{patch}/data/pt_BR/champion/{key}.json',
                   'label': f"Riot Data Dragon — {data['name']}", 'patch': patch,
                   'accessed_at': date.today().isoformat()},
        'facts': facts, 'tips': tips, 'profile': profile,
        'official_tips': {'own': [plain(tip) for tip in data.get('allytips', [])],
                          'against': [plain(tip) for tip in data.get('enemytips', [])]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', required=True, help='Explicit Data Dragon version, e.g. 16.20.1')
    parser.add_argument('--cache-dir', type=Path, help='Optional cache of official champion JSON records')
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', args.patch):
        parser.error('Invalid patch')
    catalog_url = f'https://ddragon.leagueoflegends.com/cdn/{args.patch}/data/pt_BR/champion.json'
    catalog = fetch_json(catalog_url)['data']
    templates = json.loads((ROOT / 'lane_coach/data/profile_templates.json').read_text(encoding='utf-8'))
    output = ROOT / 'lane_coach/data/champions'
    images = ROOT / 'lane_coach/static/champions'
    with TemporaryDirectory(prefix='lane-coach-import-') as temporary:
        staging = Path(temporary)
        (staging / 'champions').mkdir()
        (staging / 'images').mkdir()

        def import_one(key):
            cache = args.cache_dir / f'{key}.json' if args.cache_dir else None
            data = json.loads(cache.read_text(encoding='utf-8')) if cache and cache.exists() else fetch_json(
                f'https://ddragon.leagueoflegends.com/cdn/{args.patch}/data/pt_BR/champion/{key}.json')['data'][key]
            if data['id'] != key or data.get('version') != args.patch or len(data['spells']) != 4:
                raise ValueError(f'Invalid official record: {key}')
            previous = output / f'{key}.json'
            existing = json.loads(previous.read_text(encoding='utf-8')) if previous.exists() else None
            record = make_record(data, args.patch, templates, existing)
            (staging / 'champions' / f'{key}.json').write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            image = images / f'{key}.jpg'
            if not image.exists():
                with urlopen(f'https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{key}_0.jpg', timeout=30) as response:
                    raw = response.read(2_000_001)
                if not raw.startswith(b'\xff\xd8') or len(raw) > 2_000_000:
                    raise ValueError(f'Invalid image: {key}')
                (staging / 'images' / f'{key}.jpg').write_bytes(raw)
            return key

        with ThreadPoolExecutor(max_workers=6) as executor:
            for index, key in enumerate(executor.map(import_one, sorted(catalog)), 1):
                if index % 30 == 0:
                    print(f'Imported {index}/{len(catalog)}', flush=True)
        # Validate the complete staged roster before publishing any generated file.
        base = KnowledgeBase(staging / 'champions')
        if set(base.champions) != set(catalog):
            raise ValueError('Incomplete roster')
        output.mkdir(parents=True, exist_ok=True)
        images.mkdir(parents=True, exist_ok=True)
        for path in (staging / 'champions').glob('*.json'):
            (output / path.name).write_bytes(path.read_bytes())
        for path in (staging / 'images').glob('*.jpg'):
            (images / path.name).write_bytes(path.read_bytes())
        manifest = {'patch': args.patch, 'source': catalog_url, 'champion_ids': sorted(catalog),
                    'image_source': 'https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{id}_0.jpg'}
        (ROOT / 'lane_coach/data/roster.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Complete roster: {len(catalog)} champions. Existing authored profiles preserved.', flush=True)


if __name__ == '__main__':
    main()

"""Download official ability icons without changing champion content."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def download(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return response.read(1_000_001)
        except HTTPError as error:
            if error.code < 500 or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise


def stage_icons(data, patch, staging):
    """Use official image filenames, never guess a spell filename from its key."""
    key = data['id']
    if not re.fullmatch(r'[A-Za-z0-9]+', key) or not re.fullmatch(r'\d+\.\d+\.\d+', patch):
        raise ValueError('Invalid champion or patch')
    if data.get('version') != patch or len(data['spells']) != 4:
        raise ValueError(f'Invalid official record: {key}')
    spells = {'P': data['passive'], **dict(zip('QWER', data['spells']))}
    sources = {}
    for ability, spell in spells.items():
        filename = spell['image']['full']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.png', filename):
            raise ValueError(f'Invalid icon filename: {key}.{ability}')
        group = 'passive' if ability == 'P' else 'spell'
        url = f'https://ddragon.leagueoflegends.com/cdn/{patch}/img/{group}/{filename}'
        raw = download(url)
        if not raw.startswith(PNG_SIGNATURE) or len(raw) > 1_000_000:
            raise ValueError(f'Invalid icon: {key}.{ability}')
        target = staging / patch / key / f'{ability}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        sources[ability] = url
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', required=True)
    parser.add_argument('--cache-dir', type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', args.patch):
        parser.error('Invalid patch')
    manifest = json.loads((ROOT / 'lane_coach/data/roster.json').read_text(encoding='utf-8'))
    if manifest['patch'] != args.patch:
        parser.error('Patch must match the local roster')
    with TemporaryDirectory(prefix='lane-coach-icons-') as temporary:
        staging = Path(temporary)

        def import_one(key):
            cache = args.cache_dir / f'{key}.json' if args.cache_dir else None
            if cache and cache.exists():
                data = json.loads(cache.read_text(encoding='utf-8'))
            else:
                document = json.loads(download(f'https://ddragon.leagueoflegends.com/cdn/{args.patch}/data/pt_BR/champion/{key}.json'))
                data = {**document['data'][key], 'version': document['version']}
            if data['id'] != key:
                raise ValueError(f'Wrong champion: {key}')
            return key, stage_icons(data, args.patch, staging)

        sources = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            for index, (key, icons) in enumerate(executor.map(import_one, manifest['champion_ids']), 1):
                sources[key] = icons
                if index % 30 == 0:
                    print(f'Imported {index}/{len(manifest["champion_ids"])} kits', flush=True)
        (staging / args.patch / 'sources.json').write_text(
            json.dumps(sources, indent=2) + '\n', encoding='utf-8')
        # Publish only after every kit has downloaded successfully.
        output = ROOT / 'lane_coach/static/abilities'
        for path in staging.rglob('*'):
            if path.is_file():
                target = output / path.relative_to(staging)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(f'Complete: {len(sources) * 5} official icons. Champion content unchanged.', flush=True)


if __name__ == '__main__':
    main()

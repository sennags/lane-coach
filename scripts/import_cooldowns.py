"""Add official cooldown data without replacing champion coaching or descriptions."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lane_coach.cooldowns import spell_cooldowns
from lane_coach.knowledge import KnowledgeBase


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, help='Optional official response cache')
    args = parser.parse_args()
    base = KnowledgeBase()
    staged = {}

    def load(champion):
        key = champion['id']
        cache = args.cache_dir / f'{key}.json' if args.cache_dir else None
        if cache and cache.exists():
            document = json.loads(cache.read_text(encoding='utf-8'))
        else:
            with urlopen(champion['source']['url'], timeout=30) as response:
                document = json.load(response)
            if cache:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(document, ensure_ascii=False), encoding='utf-8')
        official = document['data'][key]
        if document['version'] != champion['source']['patch'] or official['id'] != key or len(official['spells']) != 4:
            raise ValueError(f'Official snapshot mismatch: {key}')
        spells = dict(zip('QWER', official['spells']))
        for fact in champion['facts']:
            fact['cooldown'] = spell_cooldowns(spells[fact['ability']]) if fact['ability'] != 'P' else None
        return key, champion

    # Finish all reads before mutating the roster. No full import or database access.
    with ThreadPoolExecutor(max_workers=4) as executor:
        for index, (key, champion) in enumerate(executor.map(load, base.champions.values()), 1):
            staged[key] = champion
            if index % 30 == 0:
                print(f'Cooldowns {index}/{len(base.champions)}', flush=True)
    for key, champion in staged.items():
        (ROOT / 'lane_coach/data/champions' / f'{key}.json').write_text(
            json.dumps(champion, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Imported cooldown data for {len(staged)} champions; other fields preserved.')


if __name__ == '__main__':
    main()

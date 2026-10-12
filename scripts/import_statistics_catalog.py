"""Import numeric champion IDs and item labels for the local statistics patch."""
import argparse
import json
import re
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def fetch(patch, name):
    with urlopen(f'https://ddragon.leagueoflegends.com/cdn/{patch}/data/pt_BR/{name}.json', timeout=20) as response:
        result = json.load(response)
    if result.get('version') != patch or not isinstance(result.get('data'), dict):
        raise ValueError('Invalid official catalog')
    return result['data']


def main():
    manifest = json.loads((ROOT / 'lane_coach/data/roster.json').read_text(encoding='utf-8'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patch', default=manifest['patch'])
    patch = parser.parse_args().patch
    if not re.fullmatch(r'\d+\.\d+\.\d+', patch) or patch != manifest['patch']:
        parser.error('Use o patch do catálogo local; atualize e revise o elenco primeiro.')
    champions = {str(c['key']): c['id'] for c in fetch(patch, 'champion').values()}
    if set(champions.values()) != set(manifest['champion_ids']):
        raise ValueError('Champion IDs do not match the local roster')
    items = {key: {'name': re.sub('<[^>]+>', '', item['name']), 'gold': item['gold']['total']}
             for key, item in fetch(patch, 'item').items()
             if item.get('maps', {}).get('11') and item.get('gold', {}).get('purchasable')
             and item['gold']['total'] >= 2000 and item.get('inStore', True)}
    result = {'patch': patch, 'champions': champions, 'items': items,
              'sources': [f'https://ddragon.leagueoflegends.com/cdn/{patch}/data/pt_BR/{name}.json'
                          for name in ('champion', 'item')]}
    target = ROOT / 'lane_coach/data/statistics_catalog.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(target)
    print(f'{len(champions)} IDs e {len(items)} itens importados; perfis e habilidades preservados.')


if __name__ == '__main__':
    main()

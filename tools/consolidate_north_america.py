"""One-time migration of the 1444 mainland US/Canada setup.

Run from the repository root with --apply. Requires Pillow and numpy and the
installed vanilla province bitmap to place newly represented coastal peoples.
The migration preserves every province and every pop's culture/religion/size.
"""
from pathlib import Path
from collections import defaultdict, Counter
import json
import re
import sys
import numpy as np
from PIL import Image
from economy_audit import parse, ROOT, BASE

REGIONS = {
    'NPA': ('Pacific Northwest Peoples', 'Northwestern', 'BRITISH_COLUMBIA', 'salish athabaskan', 'WASHINGTON OREGON BRITISH_COLUMBIA'),
    'NWE': ('Western Peoples', 'Western', 'CALIFORNIA', 'paiute salish', 'CALIFORNIA NEVADA IDAHO'),
    'NSX': ('Southwestern Peoples', 'Southwestern', 'ARIZONA', 'apache navajo pueblo', 'ARIZONA NEW_MEXICO UTAH COLORADO'),
    'NGP': ('Great Plains Peoples', 'Plains', 'MONTANA', 'siouan dakota comanche caddoan', 'MONTANA WYOMING NORTH_DAKOTA SOUTH_DAKOTA NEBRASKA KANSAS OKLAHOMA TEXAS IOWA MISSOURI'),
    'NGL': ('Great Lakes and Boreal Peoples', 'Boreal', 'ONTARIO', 'algonquian cree athabaskan iroquoian', 'MINNESOTA WISCONSIN MICHIGAN ILLINOIS INDIANA OHIO ONTARIO MANITOBA SASKATCHEWAN ALBERTA'),
    'NNE': ('Northeastern Peoples', 'Northeastern', 'QUEBEC', 'algonquian iroquoian inuit', 'NEW_YORK PENNSYLVANIA NEW_JERSEY DELAWARE MARYLAND DISTRICT_OF_COLUMBIA WEST_VIRGINIA CONNECTICUT RHODE_ISLAND MASSACHUSETTS VERMONT NEW_HAMPSHIRE MAINE NEW_BRUNSWICK QUEBEC NEWFOUNDLAND'),
    'NSE': ('Southeastern Peoples', 'Southeastern', 'GEORGIA', 'muskogean cherokee siouan caddoan', 'VIRGINIA KENTUCKY TENNESSEE NORTH_CAROLINA SOUTH_CAROLINA GEORGIA FLORIDA ALABAMA MISSISSIPPI LOUISIANA ARKANSAS'),
    'NAQ': ('Arctic and Subarctic Peoples', 'Arctic', 'NUNAVUT', 'inuit athabaskan', 'ALASKA YUKON_TERRITORY NORTHWEST_TERRITORIES NUNAVUT'),
}
# Existing political tags are reused where possible. Shared culture groups are
# deliberate: political representation does not require inventing new cultures.
FACTIONS = {
    'TLG': ('Tlingit', 'Tlingit', 'ALASKA', 'salish', (92, 141, 166)),
    'X01': ('Haida', 'Haida', 'BRITISH_COLUMBIA', 'salish', (0, 180, 148)),
    'X83': ('Chinook', 'Chinookan', 'WASHINGTON', 'salish', (172, 102, 48)),
    'SHH': ('Shoshone', 'Shoshone', 'IDAHO', 'paiute', (170, 148, 75)),
    'UTE': ('Ute', 'Ute', 'UTAH', 'paiute', (220, 122, 165)),
    'CMS': ('Chumash', 'Chumash', 'CALIFORNIA', 'salish', (92, 156, 183)),
    'PUE': ('Pueblo', 'Pueblo', 'NEW_MEXICO', 'pueblo', (162, 128, 8)),
    'HOP': ('Hopi', 'Hopi', 'ARIZONA', 'pueblo', (191, 122, 66)),
    'ZUN': ('Zuni', 'Zuni', 'NEW_MEXICO', 'pueblo', (121, 164, 190)),
    'DKT': ('Dakota', 'Dakota', 'MINNESOTA', 'dakota', (130, 65, 149)),
    'PWN': ('Pawnee', 'Pawnee', 'NEBRASKA', 'caddoan', (235, 87, 114)),
    'O01': ('Osage', 'Osage', 'MISSOURI', 'siouan', (166, 126, 68)),
    'CRY': ('Cree', 'Cree', 'ONTARIO', 'cree', (61, 158, 124)),
    'OJB': ('Ojibwe', 'Ojibwe', 'MICHIGAN', 'algonquian', (214, 148, 40)),
    'WDT': ('Wendat', 'Wendat', 'ONTARIO', 'iroquoian', (131, 109, 178)),
    'IRO': ('Iroquoian Nations', 'Iroquoian', 'NEW_YORK', 'iroquoian', (87, 182, 80)),
    'L03': ('Lenape', 'Lenape', 'NEW_JERSEY', 'algonquian', (184, 126, 160)),
    'MKQ': ("Mi'kmaq", "Mi'kmaq", 'NEW_BRUNSWICK', 'algonquian', (182, 79, 63)),
    'CHE': ('Cherokee', 'Cherokee', 'TENNESSEE', 'cherokee', (135, 89, 52)),
    'C03': ('Choctaw', 'Choctaw', 'MISSISSIPPI', 'muskogean', (89, 139, 68)),
    'C05': ('Caddo', 'Caddoan', 'ARKANSAS', 'caddoan', (165, 96, 52)),
    'CLS': ('Calusa', 'Calusa', 'FLORIDA', 'muskogean', (64, 153, 166)),
}

def read(p):
    return p.read_text(encoding='utf-8-sig')

def write(p, text, bom=False):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8-sig' if bom else 'utf-8', newline='\n')

def province_centres():
    # Sample exact pixels, preserving RGB province identifiers.
    rgb = np.asarray(Image.open(BASE / 'map_data/provinces.png').convert('RGB'))[::4, ::4]
    codes = (rgb[:, :, 0].astype(np.uint32) << 16) | (rgb[:, :, 1].astype(np.uint32) << 8) | rgb[:, :, 2]
    colors, inverse = np.unique(codes, return_inverse=True)
    inverse = inverse.ravel()
    ys, xs = np.indices(codes.shape)
    counts = np.bincount(inverse)
    cx = np.bincount(inverse, weights=xs.ravel()) / counts
    cy = np.bincount(inverse, weights=ys.ravel()) / counts
    return {f'x{c:06X}': (float(x), float(y)) for c, x, y in zip(colors, cx, cy)}

def main():
    if '--apply' not in sys.argv:
        raise SystemExit('Use --apply to run this one-time migration.')
    output = ROOT / 'common/country_definitions/aoc_north_america.txt'
    if output.exists():
        raise SystemExit('North America migration already applied; use audit_north_america.py.')
    region_by_state = {'s:STATE_' + s: tag for tag, data in REGIONS.items() for s in data[4].split()}
    path = ROOT / 'common/history/states/00_states.txt'
    text = read(path)
    states = {s.key: s for s in parse(text)[0].value if s.key in region_by_state}
    assert set(states) == set(region_by_state)
    centres = province_centres()
    mapping = {}  # (state, old tag) -> province-count-weighted new owners
    new_owners = {}
    before_provinces = {}
    old_tags = set()
    patches = []
    for key, state in states.items():
        region = region_by_state[key]
        short = key.removeprefix('s:STATE_')
        originals = state.children('create_state')
        all_provs = [p for n in originals for p in n.words('owned_provinces')]
        before_provinces[key] = sorted(set(all_provs))
        # Geographic bands supply territory for factions absent from the old
        # setup; existing faction provinces otherwise retain their owners.
        coords = [centres[p] for p in all_provs if p in centres]
        ymin, ymax = min(y for x, y in coords), max(y for x, y in coords)
        xmin, xmax = min(x for x, y in coords), max(x for x, y in coords)
        owners = defaultdict(list)
        for n in originals:
            old = n.scalar('country').removeprefix('c:')
            old_tags.add(old)
            destinations = Counter()
            for prov in n.words('owned_provinces'):
                x, y = centres.get(prov, ((xmin+xmax)/2, (ymin+ymax)/2))
                target = old if old in FACTIONS else region
                if old == 'LKT': target = 'DKT'
                if old in {'T45', 'T59', 'X31'}: target = 'WDT'
                if old == 'O01' and short == 'INDIANA': target = region
                if short == 'ALASKA' and x > xmin + .78*(xmax-xmin) and y > ymin + .65*(ymax-ymin): target = 'TLG'
                # Haida territory is on the BC coast; Alaska fragments join
                # the Arctic grouping unless they fall in Tlingit territory.
                if short == 'ALASKA' and target == 'X01': target = 'NAQ'
                if short == 'CALIFORNIA' and y > ymin + .70*(ymax-ymin): target = 'CMS'
                if short == 'IDAHO' and old in {'N05', 'N06'}: target = 'SHH'
                if short == 'NEVADA' and y < ymin + .65*(ymax-ymin): target = 'SHH'
                if short in {'WISCONSIN', 'MICHIGAN'} and old == 'N04': target = 'OJB'
                if short == 'MINNESOTA' and old in {'N04', 'X77'}: target = 'OJB'
                if short == 'ONTARIO' and old == 'N05' and y > ymin + .65*(ymax-ymin): target = 'OJB'
                if short == 'NEW_BRUNSWICK' and x > xmin + .45*(xmax-xmin): target = 'MKQ'
                if short == 'FLORIDA' and y > ymin + .50*(ymax-ymin): target = 'CLS'
                owners[target].append(prov)
                destinations[target] += 1
            mapping[key, old] = destinations
        # The source contains overlapping ownership (including BC). Prefer
        # selected factions, then the first source assignment, exactly once.
        province_owner = {}
        for tag in sorted(owners, key=lambda t: t not in FACTIONS):
            for prov in owners[tag]: province_owner.setdefault(prov, tag)
        owners = defaultdict(list)
        for prov, tag in province_owner.items(): owners[tag].append(prov)
        for n in originals:
            old = n.scalar('country').removeprefix('c:')
            mapping[key, old] = Counter(province_owner[p] for p in n.words('owned_provinces'))
        new_owners[key] = owners
        parts = [key + ' = {']
        for tag, provinces in sorted(owners.items()):
            parts += ['\t\tcreate_state = {', f'\t\t\tcountry = c:{tag}', '\t\t\towned_provinces = { ' + ' '.join(provinces) + ' }']
            if tag in FACTIONS: parts += ['\t\t\tstate_type = incorporated']
            parts += ['\t\t}']
        # Preserve homeland declarations; claims follow the same owner mapping.
        for n in state.value:
            if n.key == 'create_state': continue
            raw = text[n.start:n.end]
            if n.key == 'add_claim' and n.value.startswith('c:'):
                old = n.value[2:]
                if (key, old) in mapping:
                    raw = '\n\t\t'.join('add_claim = c:' + t for t in mapping[key, old])
            parts.append('\t\t' + raw)
        for tag in owners:
            for culture in (FACTIONS[tag][3].split() if tag in FACTIONS else []):
                if culture not in [n.value.removeprefix('cu:') for n in state.children('add_homeland')]:
                    parts.append('\t\tadd_homeland = cu:' + culture)
        parts.append('\t}')
        patches.append((state.start, state.end, '\n'.join(parts)))
    assert set(FACTIONS) <= {t for owners in new_owners.values() for t in owners}
    for tag, data in {**REGIONS, **FACTIONS}.items():
        assert tag in new_owners['s:STATE_' + data[2]], ('unowned capital', tag, data[2])

    # Remove reused definitions rather than depending on duplicate load order.
    definitions = []
    for p in sorted((ROOT / 'common/country_definitions').glob('*.txt')):
        source = read(p)
        edits = []
        for m in re.finditer(r'(?m)^([A-Z0-9]{3})\s*\??=\s*\{', source):
            tag = m[1]
            if tag not in FACTIONS and tag not in REGIONS: continue
            if tag in REGIONS: raise AssertionError(('tag collision', tag, p))
            depth, end = 1, m.end()
            for char in source[end:]:
                end += 1
                depth += (char == '{') - (char == '}')
                if not depth: break
            edits.append((m.start(), end, '# ' + tag + ' is defined in aoc_north_america.txt'))
        for a, b, replacement in reversed(edits): source = source[:a] + replacement + source[b:]
        if edits: definitions.append((p, source))

    population_before = Counter()
    population_after = Counter()
    history_edits = []
    for folder in ('pops', 'buildings'):
        for p in sorted((ROOT / 'common/history' / folder).glob('*.txt')):
            source = read(p)
            edits = []
            for top in parse(source):
                if not isinstance(top.value, list): continue
                for state in top.value:
                    if state.key not in states: continue
                    grouped = defaultdict(list)
                    for node in state.value:
                        if not node.key.startswith('region_state:'):
                            raise AssertionError(('unexpected state history', p, state.key, node.key))
                        old = node.key.split(':')[1]
                        destinations = mapping.get((state.key, old))
                        if not destinations:
                            # Repair orphan source pop/building scopes by
                            # attaching them to the regional owner if present.
                            regional = region_by_state[state.key]
                            target = regional if regional in new_owners[state.key] else max(new_owners[state.key], key=lambda t: len(new_owners[state.key][t]))
                            destinations = Counter({target: 1})
                        if folder == 'pops':
                            for pop in node.value:
                                assert pop.key == 'create_pop'
                                size = int(pop.scalar('size'))
                                identity = (state.key, pop.scalar('culture'), pop.scalar('religion'), pop.scalar('pop_type'))
                                population_before[identity] += size
                                total = sum(destinations.values())
                                allocations = {t: size*c//total for t,c in destinations.items()}
                                remaining = size - sum(allocations.values())
                                for t in sorted(destinations, key=lambda t: (-(size*destinations[t] % total), t))[:remaining]: allocations[t] += 1
                                for tag, count in allocations.items():
                                    if not count: continue
                                    raw = source[pop.start:pop.end]
                                    size_node = pop.child('size')
                                    a, b = size_node.start-pop.start, size_node.end-pop.start
                                    raw = raw[:a] + f'size = {count}' + raw[b:]
                                    grouped[tag].append(raw)
                                    population_after[identity] += count
                        else:
                            # These mainland entries contain no buildings in
                            # the source. Still handle ownership for future use.
                            tag = max(destinations, key=destinations.get)
                            for building in node.value:
                                raw = source[building.start:building.end]
                                raw = raw.replace('c:' + old, 'c:' + tag)
                                grouped[tag].append(raw)
                    for tag in new_owners[state.key]: grouped[tag]
                    block = state.key + ' = {\n'
                    for tag, entries in sorted(grouped.items()):
                        block += '\t\tregion_state:' + tag + ' = {\n'
                        block += ''.join('\t\t\t' + raw + '\n' for raw in entries)
                        block += '\t\t}\n'
                    block += '\t}'
                    edits.append((state.start, state.end, block))
            for a, b, replacement in reversed(edits): source = source[:a] + replacement + source[b:]
            if edits: history_edits.append((p, source))
    assert population_before == population_after
    for a, b, replacement in reversed(patches): text = text[:a] + replacement + text[b:]
    write(path, text)
    for p, source in definitions + history_edits: write(p, source)
    lines = ['# 1444 North America: 20 playable factions and eight regional groupings.', '# Political consolidation is a gameplay abstraction, not a claim of unified states.', '']
    for i, (tag, data) in enumerate({**FACTIONS, **REGIONS}.items()):
        name, adj, capital, cultures = data[:4]
        color = data[4] if tag in FACTIONS else (105 + i % 4 * 14, 112 + i % 3 * 12, 106 + i % 5 * 9)
        lines += [f'{tag} = {{ # {name}', '\tcolor = { ' + ' '.join(map(str, color)) + ' }', '\tcountry_type = ' + ('unrecognized' if tag in FACTIONS else 'decentralized'), '\ttier = principality', '\tcultures = { ' + cultures + ' }', '\treligion = animist', '\tcapital = STATE_' + capital, '}', '']
    write(output, '\n'.join(lines))
    loc = ['l_english:']
    # Replace existing names at their source, avoiding localization conflicts.
    for p in (ROOT / 'localization/english').rglob('*.yml'):
        original = source = read(p)
        for tag, data in FACTIONS.items():
            for key, value in ((tag, data[0]), (tag+'_ADJ', data[1])):
                source = re.sub(r'(?m)^(\s*' + key + r':)(?:\d+)?\s*"[^"\n]*"', lambda m: m[1] + '0 "' + value + '"', source)
        if source != original: write(p, source, True)
    for tag, data in {**FACTIONS, **REGIONS}.items():
        loc += [f' {tag}:0 "{data[0]}"', f' {tag}_ADJ:0 "{data[1]}"']
    write(ROOT / 'localization/english/aoc_north_america_l_english.yml', '\n'.join(loc)+'\n', True)
    laws = ['law_monarchy', 'law_autocracy', 'law_state_religion', 'law_subjecthood', 'law_hereditary_bureaucrats', 'law_manorial_economy', 'law_isolationism']
    history = ['# Playable centralized polities using the mod\'s existing culture groups.', 'COUNTRIES = {']
    for tag in FACTIONS:
        history += [f'\tc:{tag} = {{'] + ['\t\tactivate_law = law_type:' + law for law in laws] + ['\t}']
    history += ['}']
    write(ROOT / 'common/history/countries/aoc_north_america.txt', '\n'.join(history)+'\n')
    snapshot = {'old_active_tags': sorted(old_tags), 'provinces': before_provinces, 'population': [{'identity': list(k), 'size': v} for k,v in sorted(population_before.items(), key=lambda pair: str(pair[0]))]}
    write(ROOT / 'docs/north_america_baseline.json', json.dumps(snapshot, indent=2)+'\n')
    print(f'Consolidated {len(old_tags)} mainland tags into {len(FACTIONS)} playable + {len(REGIONS)} decentralized tags across {len(states)} states.')
    print(f'Preserved {sum(map(len,before_provinces.values()))} provinces and {sum(population_before.values())} population.')

if __name__ == '__main__': main()

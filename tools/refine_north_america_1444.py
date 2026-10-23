"""Apply documented homeland polygons to explicit game provinces.

python tools/refine_north_america_1444.py --apply

Uses exact province pixel centroids from the installed vanilla bitmap. Output
is frozen in docs/north_america_1444_provinces.json for independent validation.
Population is transferred by province overlap, retaining each state's culture,
religion, pop type and total. Source-linked profiles are authored separately.
"""
from collections import Counter, defaultdict
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from consolidate_north_america import ROOT, BASE, FACTIONS, REGIONS, read, parse

PROFILE = ROOT / 'tools/north_america_1444_homelands.json'
MANIFEST = ROOT / 'docs/north_america_1444_provinces.json'


def save(path, text):
    original = path.read_bytes() if path.exists() else b''
    if original.count(b'\r\n') > original.count(b'\n') / 2:
        text = text.replace('\n', '\r\n')
    prefix = b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b''
    path.write_bytes(prefix + text.encode('utf-8'))


def inside(point, polygon):
    x, y = point
    result = False
    previous = polygon[-1]
    for current in polygon:
        ax, ay = previous
        bx, by = current
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            result = not result
        previous = current
    return result


def bitmap_data():
    # All 61 mainland starting regions fit this rectangle, including the
    # represented Aleutians and Arctic islands. Do not subsample small islands.
    rgb = np.asarray(Image.open(BASE / 'map_data/provinces.png').convert('RGB'))[:1600, :3000]
    codes = (rgb[:, :, 0].astype(np.uint32) << 16) | (rgb[:, :, 1].astype(np.uint32) << 8) | rgb[:, :, 2]
    colors, inverse = np.unique(codes, return_inverse=True)
    inverse = inverse.ravel()
    yy, xx = np.indices(codes.shape)
    counts = np.bincount(inverse)
    cx = np.bincount(inverse, weights=xx.ravel()) / counts / 4
    cy = np.bincount(inverse, weights=yy.ravel()) / counts / 4
    centres = {f'x{c:06X}': (float(x), float(y)) for c, x, y in zip(colors, cx, cy)}
    return codes, centres


def preview(ownership, codes, output):
    lookup = np.full((16777216, 3), [25, 40, 53], dtype=np.uint8)
    for state, owners in ownership.items():
        for tag, provinces in owners.items():
            color = FACTIONS[tag][4] if tag in FACTIONS else (99, 111, 112)
            for p in provinces: lookup[int(p[1:], 16)] = color
    im = Image.fromarray(lookup[codes])
    # State boundaries provide orientation; province boundaries are lightened
    # within playable territories to make individual assignments reviewable.
    owner_codes = np.zeros(16777216, dtype=np.uint8)
    state_codes = np.zeros(16777216, dtype=np.uint8)
    for i, (state, owners) in enumerate(ownership.items(), 1):
        for tag, provinces in owners.items():
            for p in provinces:
                state_codes[int(p[1:], 16)] = i
                if tag in FACTIONS: owner_codes[int(p[1:], 16)] = 1 + list(FACTIONS).index(tag)
    state_map = state_codes[codes]
    play_map = owner_codes[codes]
    arr = np.array(im)
    border = np.zeros(codes.shape, dtype=bool)
    border[:, 1:] |= state_map[:, 1:] != state_map[:, :-1]
    border[1:, :] |= state_map[1:, :] != state_map[:-1, :]
    border &= state_map != 0
    arr[border] = (40, 55, 63)
    province = np.zeros(codes.shape, dtype=bool)
    province[:, 1:] |= codes[:, 1:] != codes[:, :-1]
    province[1:, :] |= codes[1:, :] != codes[:-1, :]
    province &= play_map != 0
    province &= ~border
    arr[province] = (arr[province].astype(np.uint16) * 3 // 4).astype(np.uint8)
    im = Image.fromarray(arr).crop((840, 480, 2840, 1540)).resize((1600, 848), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (1970, 980), '#11202d')
    canvas.paste(im, (0, 100))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
    title = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 29)
    draw.text((24, 20), 'North America | 1444 homeland reconstruction', font=title, fill='white')
    draw.text((24, 61), f'{len(FACTIONS)} playable settlement cores | {len(REGIONS)} decentralized regional groups | province-level assignments', font=font, fill='#bac8d2')
    for i, (tag, data) in enumerate(FACTIONS.items()):
        y = 112 + i * 30
        draw.rectangle((1620, y+3, 1640, y+23), fill=data[4])
        draw.text((1652, y), data[0], font=font, fill='white')
    regional_y = 112 + len(FACTIONS) * 30 + 16
    draw.rectangle((1620, regional_y+3, 1640, regional_y+23), fill=(99, 111, 112))
    draw.text((1652, regional_y), 'Decentralized peoples', font=font, fill='white')
    for i, line in enumerate(['Research-informed game boundaries.', 'Exact 1444 frontiers are uncertain.', 'Centralized tags are a gameplay', 'abstraction; regional tags also', 'include autonomous local bands.']):
        draw.text((1620, regional_y+46+i*21), line, font=small, fill='#bac8d2')
    draw.text((24, 950), 'Sources and confidence notes: docs/north_america_1444_research.md', font=small, fill='#bac8d2')
    canvas.save(output)


def main():
    if '--apply' not in sys.argv:
        raise SystemExit('Use --apply; source-linked homeland profiles are in ' + str(PROFILE))
    profiles = json.loads(read(PROFILE))['factions']
    assert set(profiles) == set(FACTIONS)
    region_by_state = {'s:STATE_' + s: tag for tag, data in REGIONS.items() for s in data[4].split()}
    state_path = ROOT / 'common/history/states/00_states.txt'
    source = read(state_path)
    states = {s.key: s for s in parse(source)[0].value if s.key in region_by_state}
    codes, centres = bitmap_data()
    ownership = {}
    overlap = {}
    notes = []
    for state_key, state in states.items():
        short = state_key.removeprefix('s:STATE_')
        entries = state.children('create_state')
        provinces = [p for n in entries for p in n.words('owned_provinces')]
        assert len(set(provinces)) == len(provinces)
        assert all(p in centres for p in provinces), ('missing bitmap province', short)
        owners = defaultdict(list)
        selected = {}
        for p in provinces:
            candidates = [tag for tag, profile in profiles.items()
                          if short in profile['states'].split()
                          and any(inside(centres[p], polygon) for polygon in profile['polygons'])]
            if set(candidates) == {'UTE', 'PUE'}:
                # Upper Rio Grande settlement provinces take precedence over
                # the adjacent Ute seasonal/mountain homeland envelope.
                candidates = ['PUE']
                notes.append({'state': short, 'province': p, 'reason': 'Pueblo upper Rio Grande settlement core takes precedence over the adjacent Ute mountain envelope.'})
            assert len(candidates) <= 1, ('overlapping homeland profiles', short, p, candidates)
            selected[p] = candidates[0] if candidates else region_by_state[state_key]
        # Historical Lenapehoking includes all NJ. The requested political tag
        # represents a settlement core, while peripheral autonomous Lenape
        # bands share NNE. This is not an invented non-Lenape ethnic enclave.
        if short == 'NEW_JERSEY' and all(t == 'L03' for t in selected.values()):
            fringe = min(provinces, key=lambda p: centres[p][0])
            selected[fringe] = 'NNE'
            notes.append({'state': short, 'province': fringe, 'reason': 'Autonomous peripheral Lenape bands; no-whole-state gameplay constraint.'})
        for p in sorted(provinces): owners[selected[p]].append(p)
        for old in entries:
            tag = old.scalar('country')[2:]
            overlap[state_key, tag] = Counter(selected[p] for p in old.words('owned_provinces'))
        ownership[state_key] = dict(owners)
    active = {tag for owners in ownership.values() for tag in owners}
    assert active == set(FACTIONS) | set(REGIONS), ('missing factions or regional groups', active)
    for tag, profile in profiles.items():
        assert tag in ownership['s:STATE_' + profile['capital']], ('unowned capital', tag)
    for state, owners in ownership.items():
        assert not (len(owners) == 1 and next(iter(owners)) in FACTIONS), ('full-state assignment', state)
    edits = []
    for key, state in states.items():
        raw = key + ' = {\n'
        for tag, provinces in sorted(ownership[key].items()):
            raw += '\t\tcreate_state = {\n\t\t\tcountry = c:' + tag + '\n'
            raw += '\t\t\towned_provinces = { ' + ' '.join(provinces) + ' }\n'
            if tag in FACTIONS: raw += '\t\t\tstate_type = incorporated\n'
            raw += '\t\t}\n'
        homelands = {n.value.removeprefix('cu:') for n in state.children('add_homeland')}
        for node in state.value:
            if node.key == 'create_state': continue
            if node.key == 'add_claim' and node.value.startswith('c:') and node.value[2:] in FACTIONS and node.value[2:] not in ownership[key]:
                continue  # Do not retain imported claims for removed expansion.
            raw += '\t\t' + source[node.start:node.end] + '\n'
        for tag in ownership[key]:
            if tag not in FACTIONS: continue
            for culture in FACTIONS[tag][3].split():
                if culture not in homelands:
                    raw += '\t\tadd_homeland = cu:' + culture + '\n'
                    homelands.add(culture)
        raw += '\t}'
        edits.append((state.start, state.end, raw))
    for a, b, raw in reversed(edits): source = source[:a] + raw + source[b:]
    planned = [(state_path, source)]
    before = Counter()
    after = Counter()
    for folder in ('pops', 'buildings'):
        for path in sorted((ROOT / 'common/history' / folder).glob('*.txt')):
            source = read(path)
            edits = []
            for top in parse(source):
                if not isinstance(top.value, list): continue
                for state in top.value:
                    if state.key not in states: continue
                    grouped = {tag: [] for tag in ownership[state.key]}
                    for region in state.value:
                        old = region.key.removeprefix('region_state:')
                        destinations = overlap[state.key, old]
                        if folder == 'buildings':
                            assert not region.value, ('nonempty building history needs explicit migration', path, state.key, old)
                            continue
                        for pop in region.value:
                            assert pop.key == 'create_pop'
                            size = int(pop.scalar('size'))
                            identity = (state.key, pop.scalar('culture'), pop.scalar('religion'), pop.scalar('pop_type'))
                            before[identity] += size
                            total = sum(destinations.values())
                            shares = {t: size*c//total for t, c in destinations.items()}
                            remaining = size - sum(shares.values())
                            for tag in sorted(destinations, key=lambda t: (-(size*destinations[t] % total), t))[:remaining]: shares[tag] += 1
                            for tag, count in shares.items():
                                if not count: continue
                                raw = source[pop.start:pop.end]
                                sn = pop.child('size')
                                a, b = sn.start-pop.start, sn.end-pop.start
                                grouped[tag].append(raw[:a]+f'size = {count}'+raw[b:])
                                after[identity] += count
                    # Combine identical pop templates to avoid proliferating
                    # create_pop statements on repeated border refinements.
                    if folder == 'pops':
                        for tag, entries in grouped.items():
                            combined = {}
                            for raw in entries:
                                pop = parse(raw)[0]
                                template = tuple((n.key, str(n.value)) for n in pop.value if n.key != 'size')
                                if template not in combined: combined[template] = [raw, 0]
                                combined[template][1] += int(pop.scalar('size'))
                            grouped[tag] = []
                            for raw, size in combined.values():
                                pop = parse(raw)[0]; sn = pop.child('size')
                                grouped[tag].append(raw[:sn.start]+f'size = {size}'+raw[sn.end:])
                    raw = state.key + ' = {\n'
                    for tag, entries in sorted(grouped.items()):
                        raw += '\t\tregion_state:' + tag + ' = {\n'
                        raw += ''.join('\t\t\t' + pop + '\n' for pop in entries)
                        raw += '\t\t}\n'
                    raw += '\t}'
                    edits.append((state.start, state.end, raw))
            for a, b, raw in reversed(edits): source = source[:a] + raw + source[b:]
            if edits: planned.append((path, source))
    assert before == after
    definitions_path = ROOT / 'common/country_definitions/aoc_north_america.txt'
    source = read(definitions_path)
    edits = []
    for country in parse(source):
        if country.key not in profiles: continue
        capital = country.child('capital')
        edits.append((capital.start, capital.end, 'capital = STATE_' + profiles[country.key]['capital']))
    for a, b, raw in reversed(edits): source = source[:a] + raw + source[b:]
    planned.append((definitions_path, source))
    # Complete checks before writing any game files.
    for path, text in planned: parse(text)
    for path, text in planned: save(path, text)
    manifest = {'method': json.loads(read(PROFILE))['method'], 'gameplay_exceptions': notes,
                'states': {state.removeprefix('s:'): dict(sorted(owners.items())) for state, owners in sorted(ownership.items())}}
    save(MANIFEST, json.dumps(manifest, indent=2)+'\n')
    counts = Counter()
    for owners in ownership.values():
        for tag, provinces in owners.items(): counts[tag] += len(provinces)
    for tag in FACTIONS: print(f'{tag}: {counts[tag]} provinces in ' + ', '.join(state.removeprefix('s:STATE_') for state, owners in ownership.items() if tag in owners))
    print(f'Preserved {sum(counts.values())} provinces and {sum(before.values())} population.')
    preview(ownership, codes, ROOT / 'docs/north_america_1444_map.png')


if __name__ == '__main__': main()

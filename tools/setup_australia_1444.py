"""One-time Australian ownership migration. Run with --apply; audit separately.

Preserves province coverage and each pop's attributes and total size. Existing
Kulin pops are divided proportionally when their territory is split.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
import re
import sys
from economy_audit import ROOT, parse

STATES = ['NEW_SOUTH_WALES', 'VICTORIA', 'TASMANIA', 'QUEENSLAND',
          'SOUTH_AUSTRALIA', 'WESTERN_AUSTRALIA', 'NORTHERN_TERRITORY']
FACTIONS = {
    'NNG': ('Noongar', 'WESTERN_AUSTRALIA', (209, 160, 107)),
    'KAU': ('Kaurna', 'SOUTH_AUSTRALIA', (245, 212, 134)),
    'GML': ('Gamilaraay', 'NEW_SOUTH_WALES', (77, 164, 68)),
    'K16': ('Kulin', 'VICTORIA', (168, 106, 62)),
    'Y06': ('Yolngu', 'NORTHERN_TERRITORY', (94, 166, 180)),
    'T19': ('Tiwi', 'NORTHERN_TERRITORY', (166, 78, 65)),
    'GDT': ('Gunditjmara', 'VICTORIA', (85, 133, 102)),
}
# Southwest Victorian province centroids, inspected against the installed map.
# These were formerly assigned to the broad Kulinic language-family tag.
GUNDITJMARA = set('x0B39E0 x157463 x3AEC95 x49E501 x4F1BC4 x506E5E xA03BDF xCC9C60 xCCBB53'.split())

def read(p):
    return p.read_text(encoding='utf-8-sig')

def write(p, text, bom=False):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8-sig' if bom else 'utf-8', newline='\n')

def nodes(text):
    # Maintain character offsets while supporting converter conditional keys.
    return parse(text.replace('?=', ' ='))

def patch(text, patches):
    for start, end, replacement in sorted(patches, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text

def target(state, old, province):
    if state == 's:STATE_VICTORIA' and province in GUNDITJMARA:
        return 'GDT'
    if old == 'K16' and state != 's:STATE_VICTORIA':
        return 'AUP'
    return old if old in FACTIONS else 'AUP'

def main():
    if '--apply' not in sys.argv:
        raise SystemExit('Run with --apply for the one-time migration.')
    output = ROOT/'common/country_definitions/aoc_australia.txt'
    if output.exists():
        raise SystemExit('Already applied. Run audit_australia.py instead.')
    keys = {'s:STATE_'+s for s in STATES}
    path = ROOT/'common/history/states/00_states.txt'
    text = read(path)
    selected = [n for n in nodes(text)[0].value if n.key in keys]
    assert len(selected) == len(keys)
    mapping, owners, baseline, patches = {}, {}, {}, []
    for state in selected:
        assigned = {}
        for old in state.children('create_state'):
            tag = old.scalar('country')[2:]
            for province in old.words('owned_provinces'):
                destination = target(state.key, tag, province)
                # Source province lists contain duplicates. Prefer the named
                # playable nation over the remainder when claims overlap.
                if province not in assigned or assigned[province] == 'AUP':
                    assigned[province] = destination
        for old in state.children('create_state'):
            mapping[state.key, old.scalar('country')[2:]] = Counter(assigned[p] for p in set(old.words('owned_provinces')))
        baseline[state.key] = {'provinces': sorted(assigned)}
        groups = defaultdict(list)
        for province, tag in assigned.items():
            groups[tag].append(province)
        owners[state.key] = groups
        parts = [state.key+' = {']
        for tag, provinces in sorted(groups.items()):
            parts += ['\t\tcreate_state = {', '\t\t\tcountry = c:'+tag,
                      '\t\t\towned_provinces = { '+' '.join(provinces)+' }',
                      '\t\t\tstate_type = '+('incorporated' if tag in FACTIONS else 'unincorporated'), '\t\t}']
        parts += ['\t\tadd_homeland = cu:aborigine', '\t}']
        patches.append((state.start, state.end, '\n'.join(parts)))
    write(path, patch(text, patches))
    path = ROOT/'common/history/pops/new_pops.txt'
    text = read(path)
    patches = []
    for state in nodes(text)[0].value:
        if state.key not in keys:
            continue
        groups = defaultdict(list)
        totals = Counter()
        for region in state.value:
            old = region.key.split(':')[1]
            destinations = mapping[state.key, old]
            for pop in region.children('create_pop'):
                size = int(pop.scalar('size'))
                attributes = tuple((n.key, n.value) for n in pop.value if n.key != 'size')
                totals[attributes] += size
                ranked = sorted(destinations)
                counts = {tag: size*destinations[tag]//sum(destinations.values()) for tag in ranked}
                for tag in sorted(ranked, key=lambda t: (-(size*destinations[t] % sum(destinations.values())), t))[:size-sum(counts.values())]:
                    counts[tag] += 1
                for tag, count in counts.items():
                    if count:
                        groups[tag].append('\t\t\tcreate_pop = {\n'+''.join('\t\t\t\t'+k+' = '+v+'\n' for k,v in attributes)+'\t\t\t\tsize = '+str(count)+'\n\t\t\t}')
        baseline[state.key]['pops'] = [[list(a), count] for a,count in sorted(totals.items())]
        parts = [state.key+' = {']
        for tag, pops in sorted(groups.items()):
            parts += ['\t\tregion_state:'+tag+' = {', *pops, '\t\t}']
        parts += ['\t}']
        patches.append((state.start, state.end, '\n'.join(parts)))
    write(path, patch(text, patches))
    # Replace empty source building scopes with the actual new state owners.
    path = ROOT/'common/history/buildings/13_australasia.txt'
    text = read(path)
    patches = []
    for state in nodes(text)[0].value:
        if state.key in keys:
            assert all(not n.value for n in state.value), 'Unexpected buildings: migrate explicitly'
            parts = [state.key+' = {']+['\t\tregion_state:'+t+' = { }' for t in sorted(owners[state.key])]+['\t}']
            patches.append((state.start, state.end, '\n'.join(parts)))
    write(path, patch(text, patches))
    # Move existing definitions, avoiding duplicate country keys.
    for path in (ROOT/'common/country_definitions').glob('*.txt'):
        text = read(path)
        if not re.search(r'^(?:'+'|'.join(FACTIONS)+r')\s*\??=', text, re.M):
            continue
        patches = [(n.start,n.end,'') for n in nodes(text) if n.key in FACTIONS]
        if patches:
            write(path, patch(text, patches))
    definitions = ['# 1444 gameplay centralization; not a claim of historical statehood.']
    for tag,(name,capital,color) in FACTIONS.items():
        definitions.append(f'{tag} = {{ # {name}\n\tcolor = {{ {color[0]} {color[1]} {color[2]} }}\n\tcountry_type = unrecognized\n\ttier = principality\n\tcultures = {{ aborigine }}\n\treligion = animist\n\tcapital = STATE_{capital}\n}}')
    definitions.append('AUP = {\n\tcolor = { 144 120 87 }\n\tcountry_type = decentralized\n\ttier = principality\n\tcultures = { aborigine }\n\treligion = animist\n\tcapital = STATE_NORTHERN_TERRITORY\n}')
    write(output, '\n\n'.join(definitions)+'\n')
    laws = ['monarchy','autocracy','state_religion','subjecthood','hereditary_bureaucrats','manorial_economy','isolationism']
    write(ROOT/'common/history/countries/aoc_australia.txt', '# Playable government defaults follow the existing indigenous 1444 setup.\nCOUNTRIES = {\n'+''.join('\tc:'+tag+' = {\n'+''.join('\t\tactivate_law = law_type:law_'+law+'\n' for law in laws)+'\t}\n' for tag in FACTIONS)+'}\n')
    lines = ['l_english:']
    for tag,(name,_,_) in FACTIONS.items():
        lines += [f' {tag}:0 "{name}"', f' {tag}_ADJ:0 "{name}"']
    lines += [' AUP:0 "Aboriginal Australian Peoples"', ' AUP_ADJ:0 "Aboriginal Australian"']
    write(ROOT/'localization/english/replace/zz_aoc_australia_l_english.yml', '\n'.join(lines)+'\n', True)
    banners = '# Abstract gameplay banners, not historical flags.\nNNG = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = yellow\n\tcolor2 = black\n}\nGML = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = green\n\tcolor2 = white\n}\nK16 = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = red\n\tcolor2 = yellow\n}\nY06 = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = blue\n\tcolor2 = white\n}\nT19 = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = red\n\tcolor2 = black\n}\nGDT = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = green\n\tcolor2 = yellow\n}\nAUP = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = brown\n\tcolor2 = white\n}\n'
    write(ROOT/'common/coat_of_arms/coat_of_arms/aoc_australia.txt', banners)
    write(ROOT/'docs/australia_1444_baseline.json', json.dumps(baseline, indent=2)+'\n')
    print('Applied Australian setup. Run tools/audit_australia.py.')

if __name__ == '__main__':
    main()

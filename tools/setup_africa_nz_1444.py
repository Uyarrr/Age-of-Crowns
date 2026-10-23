"""Consolidate African decentralized countries and New Zealand (--apply)."""
from collections import Counter, defaultdict
import hashlib
import json
import re
import sys
from economy_audit import ROOT, BASE, parse
from setup_australia_1444 import patch, read

PLAYABLE = dict(
    MAL='Mali', BOR='Bornu', JLF='Jolof', BEN='Benin', OYO='Oyo', GAO='Songhai',
    S37='Yatenga', T93='Wagadugu', KON='Kongo', LBA='Luba', LND='Lunda',
    KBA='Kuba', BUG='Buganda', BNY='Bunyoro', RWD='Rwanda', BRD='Burundi',
    S41='Kilwa', S44='Mutapa', U73='Butua', U79='Sofala', U52='Pate',
    V57='Mombasa', V80='Malindi', ASH='Asante', DAH='Dahomey', ZUL='Zulu',
    XHO='Xhosa', TSW='Tswana', MSI='Maasai', MRV='Maravi', U83='Sakalava',
    ZND='Azande', WAD='Wadai')
NZ = {'s:STATE_NORTH_ISLAND', 's:STATE_SOUTH_ISLAND'}

def nodes(text):
    text = text.replace('?=', ' =')
    return parse(re.sub(r'\b(?:rgb|hsv360|hsv)(?=\s*\{)', lambda m:' '*len(m[0]), text))

def write(path, text, bom=False):
    # Preserve original line-ending convention in existing files.
    ending = '\r\n' if path.exists() and b'\r\n' in path.read_bytes() else '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8-sig' if bom else 'utf-8', newline=ending)

def state_nodes(text):
    return [s for top in nodes(text) if isinstance(top.value,list) for s in top.value
            if s.key.startswith('s:STATE_')]

def pop_totals(state):
    totals = Counter()
    for region in state.value:
        for pop in region.children('create_pop'):
            attrs = tuple((n.key,n.value) for n in pop.value if n.key != 'size')
            totals[attrs] += int(pop.scalar('size'))
    return [[list(map(list, attrs)),size] for attrs,size in sorted(totals.items())]

def main():
    if '--apply' not in sys.argv:
        raise SystemExit('Use --apply to run the one-time migration.')
    output = ROOT/'common/country_definitions/aoc_africa_playable.txt'
    if output.exists():
        raise SystemExit('Already applied; run audit_africa_nz.py.')
    region_path = BASE/'common/strategic_regions/african_strategic_regions.txt'
    africa = {'s:'+s for n in nodes(read(region_path)) for s in n.words('states')}
    definitions, definition_paths = {}, {}
    for path in sorted((ROOT/'common/country_definitions').glob('*.txt')):
        source = read(path)
        for n in nodes(source):
            if re.match(r'\w+\s*\?=', source[n.start:n.end]) and n.key in definitions:
                continue
            definitions[n.key] = n
            definition_paths[n.key] = path
    assert not ({'AFD','NPH','MZD'} & definitions.keys())
    pending, mapping, owners, baseline, originals, active_before = {}, {}, {}, {}, {}, set()
    all_states = []
    for path in (ROOT/'common/history/states').glob('*.txt'):
        text = read(path)
        all_states += [(path,text,s) for s in state_nodes(text) if s.children('create_state')]
    for path,text,state in all_states:
        active_before.update(n.scalar('country')[2:] for n in state.children('create_state') if state.key in africa)
        if state.key not in africa|NZ:
            continue
        assert state.key not in baseline, ('Duplicate ownership state',state.key)
        groups = defaultdict(list)
        province_owner = {}
        for region in state.children('create_state'):
            old = region.scalar('country')[2:]
            if state.key in NZ:
                dest = 'NPH' if old == 'T75' else 'MZD'
            else:
                dest = 'AFD' if definitions[old].scalar('country_type') == 'decentralized' and old not in PLAYABLE else old
            mapping[state.key,old] = dest
            for p in region.words('owned_provinces'):
                if p not in province_owner or province_owner[p] in {'AFD','MZD'}:
                    province_owner[p] = dest
        for p,tag in province_owner.items():
            groups[tag].append(p)
        owners[state.key] = groups
        baseline[state.key] = {'provinces': sorted(province_owner)}
        originals[state.key] = (path,text,state)
    assert set(PLAYABLE) <= active_before
    retired = {old for (state,old),dest in mapping.items() if old != dest}
    active_after = {mapping.get((s.key,n.scalar('country')[2:]),n.scalar('country')[2:]) for _,_,s in all_states for n in s.children('create_state')}
    retired -= active_after
    for path,text,state in originals.values():
        parts = [state.key+' = {']
        for tag,provinces in sorted(owners[state.key].items()):
            source = next((n for n in state.children('create_state') if n.scalar('country') == 'c:'+tag),None)
            parts += ['\t\tcreate_state = {', '\t\t\tcountry = c:'+tag,
                      '\t\t\towned_provinces = { '+' '.join(provinces)+' }']
            if tag in PLAYABLE or tag == 'NPH':
                parts.append('\t\t\tstate_type = incorporated')
            elif tag in {'AFD','MZD'}:
                parts.append('\t\t\tstate_type = unincorporated')
            elif source:
                parts += ['\t\t\t'+text[n.start:n.end] for n in source.value if n.key not in {'country','owned_provinces'}]
            parts += ['\t\t}']
        parts += ['\t\t'+text[n.start:n.end] for n in state.value if n.key != 'create_state']
        parts += ['\t}']
        pending.setdefault(path,[]).append((state.start,state.end,'\n'.join(parts)))
    # Move pops and buildings to their actual owners, preserving all attributes.
    for folder in ['pops','buildings']:
        for path in (ROOT/'common/history'/folder).glob('*.txt'):
            text = read(path)
            for state in state_nodes(text):
                if state.key not in owners or not any(n.key.startswith('region_state:') for n in state.value):
                    continue
                groups = defaultdict(list)
                other = []
                for region in state.value:
                    if not region.key.startswith('region_state:'):
                        other.append(text[region.start:region.end]);continue
                    old = region.key.split(':')[1]
                    if (state.key,old) not in mapping:
                        assert not region.value, ('Unowned history with content',path,state.key,old)
                        continue
                    dest = mapping[state.key,old]
                    body = text[text.index('{',region.start)+1:region.end-1]
                    body = re.sub(r'c:'+re.escape(old)+r'\b','c:'+dest,body)
                    groups[dest].append(body)
                parts = [state.key+' = {']
                for tag,bodies in sorted(groups.items()):
                    parts += ['\t\tregion_state:'+tag+' = {', *bodies, '\t\t}']
                parts += other+['\t}']
                pending.setdefault(path,[]).append((state.start,state.end,'\n'.join(parts)))
                if folder == 'pops':
                    baseline[state.key]['pops'] = pop_totals(state)
    # Remove retired-country diplomatic clauses instead of transferring feuds
    # into a continent-wide aggregate.
    for path in (ROOT/'common/history/diplomacy').glob('*.txt'):
        text = read(path)
        def visit(n):
            raw = text[n.start:n.end]
            if n.key.startswith('c:') and n.key[2:] in retired:
                pending.setdefault(path,[]).append((n.start,n.end,''));return
            if n.key in {'set_relations','create_diplomatic_pact','create_subject'} and any(re.search(r'c:'+re.escape(t)+r'\b',raw) for t in retired):
                pending.setdefault(path,[]).append((n.start,n.end,''));return
            if isinstance(n.value,list):
                for child in n.value:visit(child)
        for top in nodes(text):visit(top)
    # Edit original definitions in place; retain their existing colors and tiers.
    capital_by_tag = {}
    for tag in PLAYABLE:
        owned = [s for s,groups in owners.items() if tag in groups]
        original = definitions[tag]
        capital = 's:'+original.scalar('capital')
        if capital not in owned:
            capital = max(owned,key=lambda s:len(owners[s][tag]))
        capital_by_tag[tag] = capital[2:]
        path = definition_paths[tag];text = read(path)
        raw = text[original.start:original.end]
        raw = re.sub(r'country_type\s*=\s*decentralized','country_type = unrecognized',raw)
        raw = re.sub(r'capital\s*=\s*\w+','capital = '+capital[2:],raw)
        if tag == 'OYO':
            raw = re.sub(r'cultures\s*=\s*\{[^}]*\}', 'cultures = { yoruba edo }',raw)
        if tag == 'S41':
            raw = re.sub(r'cultures\s*=\s*\{[^}]*\}', 'cultures = { swahili yao }',raw)
        pending.setdefault(path,[]).append((original.start,original.end,raw))
    aggregate_cultures = sorted({cu for (state,old),dest in mapping.items() if dest=='AFD' for cu in definitions[old].words('cultures')})
    new_defs = 'AFD = {\n\tcolor = { 150 133 99 }\n\tcountry_type = decentralized\n\ttier = principality\n\tcultures = { '+' '.join(aggregate_cultures)+' }\n\treligion = animist\n\tcapital = STATE_EQUATEUR\n}\n'
    new_defs += 'NPH = {\n\tcolor = { 160 56 51 }\n\tcountry_type = unrecognized\n\ttier = principality\n\tcultures = { maori }\n\treligion = animist\n\tcapital = STATE_NORTH_ISLAND\n}\nMZD = {\n\tcolor = { 109 143 121 }\n\tcountry_type = decentralized\n\ttier = principality\n\tcultures = { maori }\n\treligion = animist\n\tcapital = STATE_SOUTH_ISLAND\n}\n'
    # Record non-target state blocks so the audit can prove they were untouched.
    untouched = defaultdict(list)
    for _,text,s in all_states:
        if s.key not in owners:
            untouched[s.key].append(hashlib.sha256(text[s.start:s.end].encode()).hexdigest())
    pending = {p:[(start,end,re.sub(r'[ \t]+$', '',replacement,flags=re.M))
                  for start,end,replacement in patches] for p,patches in pending.items()}
    for path,patches in pending.items():
        result = patch(read(path),patches)
        nodes(result)
    for path,patches in pending.items():
        result = patch(read(path),patches)
        if path.parent.name == 'diplomacy':
            result = re.sub(r'^[ \t]+$', '', result, flags=re.M)
        write(path,result)
    write(output,new_defs)
    muslim = {'MAL','BOR','JLF','GAO','S41','U79','U52','V57','V80','WAD'}
    laws = ['monarchy','autocracy','state_religion','subjecthood','hereditary_bureaucrats','manorial_economy','isolationism']
    history = ['COUNTRIES = {']
    for tag in [*PLAYABLE,'NPH']:
        history += ['\tc:'+tag+' = {']
        if tag in muslim:
            history += ['\t\tset_state_religion = rel:sunni']
        history += ['\t\tactivate_law = law_type:law_'+law for law in laws]+['\t}']
    history += ['}']
    write(ROOT/'common/history/countries/aoc_africa_nz.txt','\n'.join(history)+'\n')
    names = {**PLAYABLE,'AFD':'African Peoples','NPH':'Ngāpuhi','MZD':'Māori Peoples'}
    lines = ['l_english:']
    for tag,name in names.items():lines += [f' {tag}:0 "{name}"',f' {tag}_ADJ:0 "{name}"']
    write(ROOT/'localization/english/replace/zz_aoc_africa_nz_l_english.yml','\n'.join(lines)+'\n',True)
    write(ROOT/'common/coat_of_arms/coat_of_arms/aoc_africa_nz.txt', '# Abstract gameplay banners; not historical flags.\n'+''.join(tag+' = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = '+color+'\n\tcolor2 = white\n}\n' for tag,color in [('AFD','brown'),('NPH','red'),('MZD','green')]))
    for rel in ['localization/english/replace/zz_aoc_north_america_l_english.yml','tools/consolidate_north_america.py','docs/north_america.md','docs/north_america_1444_research.md']:
        path = ROOT/rel
        write(path,read(path).replace('Rio Grande Pueblos','Pueblo'),rel.endswith('.yml'))
    summary = {'states':baseline,'untouched_states':untouched,'retired':sorted(retired),'playable':PLAYABLE,'africa_states':sorted(africa),'african_before':len(active_before),'african_after':len({t for s,groups in owners.items() if s in africa for t in groups})}
    write(ROOT/'docs/africa_nz_1444_baseline.json',json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(f'Applied: {len(PLAYABLE)} African promotions; African owners {summary["african_before"]} -> {summary["african_after"]}; New Zealand 7 -> 2.')

if __name__ == '__main__':main()

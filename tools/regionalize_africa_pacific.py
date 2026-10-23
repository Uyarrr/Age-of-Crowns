"""Split the African aggregate and consolidate Pacific islands (--apply)."""
from collections import Counter, defaultdict
import hashlib
import json
import re
import sys
from setup_africa_nz_1444 import ROOT, BASE, nodes, read, write, patch, state_nodes, pop_totals

AFRICAN_TAGS = {'AFD','AFC','AFE'}
NAMES = {'AFD':'Northern and Western African Peoples',
         'AFC':'Central African Peoples', 'AFE':'Eastern and Southern African Peoples',
         'OPD':'Pacific Island Peoples', 'HAW':'Hawaii'}
EXCLUDED = {'s:STATE_'+s for s in ['NEW_SOUTH_WALES','VICTORIA','QUEENSLAND',
    'SOUTH_AUSTRALIA','WESTERN_AUSTRALIA','NORTHERN_TERRITORY','TASMANIA',
    'NORTH_ISLAND','SOUTH_ISLAND']}

def effective_definitions():
    result,paths = {},{}
    for p in sorted((ROOT/'common/country_definitions').glob('*.txt')):
        text = read(p)
        for n in nodes(text):
            if re.match(r'\w+\s*\?=',text[n.start:n.end]) and n.key in result:
                continue
            result[n.key],paths[n.key] = n,p
    return result,paths

def signature(node):
    if isinstance(node.value,list):
        return (node.key,tuple(signature(n) for n in node.value))
    value = node.value
    if value and re.fullmatch(r'"?c:\w+"?',value):value = 'c:OWNER'
    return (node.key,value)

def building_signatures(state):
    return sorted([signature(n) for region in state.value for n in region.children('create_building')],key=repr)

def main():
    if '--apply' not in sys.argv:raise SystemExit('Use --apply.')
    out = ROOT/'docs/africa_pacific_regional_baseline.json'
    if out.exists():raise SystemExit('Already applied; use audit_africa_pacific.py.')
    definitions,definition_paths = effective_definitions()
    assert not {'AFC','AFE','OPD'} & definitions.keys()
    regions = nodes(read(BASE/'common/strategic_regions/african_strategic_regions.txt'))
    africa_by_state = {}
    for region in regions:
        tag = ('AFC' if region.key=='region_equatorial_africa' else
               'AFE' if region.key in {'region_east_africa','region_southern_africa'} else 'AFD')
        for state in region.words('states'):africa_by_state['s:'+state] = tag
    africa_by_state['s:STATE_EQUATORIA'] = 'AFE'
    oceania = next(n for n in nodes(read(BASE/'common/strategic_regions/east_asia_strategic_regions.txt')) if n.key=='region_oceania')
    pacific = ({'s:'+s for s in oceania.words('states')} | {'s:STATE_WESTERN_NEW_GUINEA','s:STATE_EASTERN_NEW_GUINEA'})-EXCLUDED
    pending,owners,mapping,baseline,unchanged,cultures = {},{},{},{},{},defaultdict(set)
    all_active = []
    for path in (ROOT/'common/history/states').glob('*.txt'):
        text = read(path)
        for state in state_nodes(text):
            if not state.children('create_state'):continue
            all_active.append((state.key,[n.scalar('country')[2:] for n in state.children('create_state')]))
            remap = {}
            for region in state.children('create_state'):
                old = region.scalar('country')[2:]
                dest = old
                if state.key in africa_by_state and old=='AFD':dest = africa_by_state[state.key]
                if state.key in pacific:
                    if state.key=='s:STATE_HAWAIIAN_ISLANDS':dest = 'HAW'
                    elif definitions[old].scalar('country_type')=='decentralized':dest = 'OPD'
                remap[old] = dest
            # Include AFD states even when its tag stays AFD to verify partition.
            affected = any(old!=dest for old,dest in remap.items()) or (state.key in africa_by_state and 'AFD' in remap)
            if not affected:
                unchanged.setdefault(state.key,[]).append(hashlib.sha256(text[state.start:state.end].encode()).hexdigest())
                continue
            assert state.key not in baseline
            groups = defaultdict(list)
            for region in state.children('create_state'):
                old=region.scalar('country')[2:];dest=remap[old]
                mapping[state.key,old]=dest
                groups[dest] += region.words('owned_provinces')
                if dest=='OPD':cultures[dest].update(definitions[old].words('cultures'))
            owners[state.key] = groups
            original_provinces = [p for values in groups.values() for p in values]
            assert len(original_provinces)==len(set(original_provinces))
            baseline[state.key]={'provinces':sorted(original_provinces), 'owners':{tag:sorted(ps) for tag,ps in groups.items()}}
            parts=[state.key+' = {']
            for tag,provinces in sorted(groups.items()):
                parts+=['\t\tcreate_state = {','\t\t\tcountry = c:'+tag,
                        '\t\t\towned_provinces = { '+' '.join(provinces)+' }']
                if tag in AFRICAN_TAGS|{'OPD'}:parts+=['\t\t\tstate_type = unincorporated']
                elif tag=='HAW':parts+=['\t\t\tstate_type = incorporated']
                else:
                    source=next(n for n in state.children('create_state') if n.scalar('country')=='c:'+tag)
                    parts+=['\t\t\t'+text[n.start:n.end] for n in source.value if n.key not in {'country','owned_provinces'}]
                parts+=['\t\t}']
            parts+=['\t\t'+text[n.start:n.end] for n in state.value if n.key!='create_state']+['\t}']
            pending.setdefault(path,[]).append((state.start,state.end,'\n'.join(parts)))
    for folder in ['pops','buildings']:
        for path in (ROOT/'common/history'/folder).glob('*.txt'):
            text=read(path)
            for state in state_nodes(text):
                if state.key not in owners:continue
                if not any(n.key.startswith('region_state:') for n in state.value):continue
                groups=defaultdict(list);other=[]
                for region in state.value:
                    if not region.key.startswith('region_state:'):
                        other.append(text[region.start:region.end]);continue
                    old=region.key.split(':')[1]
                    if (state.key,old) not in mapping:
                        assert not region.value, ('Unowned content',path,state.key,old)
                        continue
                    dest=mapping[state.key,old]
                    for child in region.value:
                        raw=text[child.start:child.end]
                        raw=re.sub(r'c:'+re.escape(old)+r'\b','c:'+dest,raw)
                        groups[dest].append(raw)
                    if folder=='pops' and dest in AFRICAN_TAGS:
                        cultures[dest].update(p.scalar('culture') for p in region.children('create_pop'))
                parts=[state.key+' = {']
                for tag,children in sorted(groups.items()):
                    parts+=['\t\tregion_state:'+tag+' = {']+['\t\t\t'+child for child in children]+['\t\t}']
                parts+=other+['\t}']
                pending.setdefault(path,[]).append((state.start,state.end,'\n'.join(parts)))
                key='pops' if folder=='pops' else 'buildings'
                assert key not in baseline[state.key], ('Duplicate history block',path,state.key)
                baseline[state.key][key]=pop_totals(state) if folder=='pops' else building_signatures(state)
    all_after={mapping.get((state,t),t) for state,tags in all_active for t in tags}
    retired={old for (state,old),dest in mapping.items() if old!=dest}-all_after
    for path in (ROOT/'common/history/diplomacy').glob('*.txt'):
        text=read(path)
        def visit(n):
            raw=text[n.start:n.end]
            if n.key.startswith('c:') and n.key[2:] in retired:
                pending.setdefault(path,[]).append((n.start,n.end,''));return
            if n.key in {'set_relations','create_diplomatic_pact','create_subject'} and any(re.search(r'c:'+re.escape(t)+r'\b',raw) for t in retired):
                pending.setdefault(path,[]).append((n.start,n.end,''));return
            if isinstance(n.value,list):
                for c in n.value:visit(c)
        for n in nodes(text):visit(n)
    capitals={'AFD':'STATE_GUINEA','AFC':'STATE_EQUATEUR','AFE':'STATE_ZAMBIA','OPD':'STATE_EASTERN_NEW_GUINEA'}
    colors={'AFD':(166,145,91),'AFC':(109,145,91),'AFE':(158,113,91),'OPD':(94,149,170)}
    def definition(tag):
        assert tag in owners['s:'+capitals[tag]], (tag,capitals[tag])
        assert cultures[tag],tag
        return tag+' = {\n\tcolor = { '+' '.join(map(str,colors[tag]))+' }\n\tcountry_type = decentralized\n\ttier = principality\n\tcultures = { '+' '.join(sorted(cultures[tag]))+' }\n\treligion = animist\n\tcapital = '+capitals[tag]+'\n}'
    afd=definitions['AFD'];path=definition_paths['AFD']
    pending.setdefault(path,[]).append((afd.start,afd.end,definition('AFD')))
    haw=definitions['HAW'];path=definition_paths['HAW'];text=read(path)
    raw=text[haw.start:haw.end]
    raw=re.sub(r'country_type\s*=\s*\w+','country_type = unrecognized',raw)
    raw=re.sub(r'religion\s*=\s*\w+','religion = animist',raw)
    raw=re.sub(r'^\s*is_named_from_capital\s*=\s*yes\s*$', '',raw,flags=re.M)
    pending.setdefault(path,[]).append((haw.start,haw.end,raw))
    for path,patches in pending.items():
        result=patch(read(path),patches)
        if path.parent.name=='diplomacy':result=re.sub(r'^[ \t]+$','',result,flags=re.M)
        nodes(result)
    for path,patches in pending.items():
        result=patch(read(path),patches)
        if path.parent.name=='diplomacy':result=re.sub(r'^[ \t]+$','',result,flags=re.M)
        write(path,result)
    write(ROOT/'common/country_definitions/aoc_africa_pacific_regions.txt','\n\n'.join(definition(t) for t in ['AFC','AFE','OPD'])+'\n')
    laws=['monarchy','autocracy','state_religion','subjecthood','hereditary_bureaucrats','manorial_economy','isolationism']
    write(ROOT/'common/history/countries/aoc_hawaii.txt','COUNTRIES = {\n\tc:HAW = {\n'+''.join('\t\tactivate_law = law_type:law_'+law+'\n' for law in laws)+'\t}\n}\n')
    lines=['l_english:']
    for tag,name in NAMES.items():lines += [f' {tag}:0 "{name}"',f' {tag}_ADJ:0 "{name}"']
    write(ROOT/'localization/english/replace/zzz_aoc_africa_pacific_l_english.yml','\n'.join(lines)+'\n',True)
    old_loc=ROOT/'localization/english/replace/zz_aoc_africa_nz_l_english.yml'
    write(old_loc,re.sub(r'^ AFD(?:_ADJ)?:[^\n]*\n','',read(old_loc),flags=re.M),True)
    write(ROOT/'common/coat_of_arms/coat_of_arms/aoc_africa_pacific_regions.txt','# Abstract gameplay banners.\n'+''.join(tag+' = {\n\tpattern = "pattern_horizontal_split_01.tga"\n\tcolor1 = '+color+'\n\tcolor2 = white\n}\n' for tag,color in [('AFC','green'),('AFE','red'),('OPD','blue')]))
    summary={'states':baseline,'unchanged_states':unchanged,'africa_regions':africa_by_state,
             'pacific_states':sorted(pacific),'retired':sorted(retired)}
    write(out,json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('Applied: three African decentralized regions, one Pacific decentralized country, unified centralized Hawaii.')

if __name__=='__main__':main()

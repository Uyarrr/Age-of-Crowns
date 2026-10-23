"""Verify the revised African partition, Pacific aggregate and unified Hawaii."""
from collections import Counter
import hashlib
import json
import re
from regionalize_africa_pacific import (ROOT, BASE, AFRICAN_TAGS, NAMES,
    effective_definitions, nodes, read, state_nodes, pop_totals, building_signatures)

def main():
    baseline=json.loads(read(ROOT/'docs/africa_pacific_regional_baseline.json'))
    wanted=baseline['states']
    definitions,_=effective_definitions()
    owners,global_owners={},set()
    unchanged={s:Counter(hashes) for s,hashes in baseline['unchanged_states'].items()}
    for path in (ROOT/'common/history/states').glob('*.txt'):
        text=read(path)
        for state in state_nodes(text):
            regions=state.children('create_state')
            if not regions:continue
            global_owners.update(n.scalar('country')[2:] for n in regions)
            if state.key not in wanted:
                digest=hashlib.sha256(text[state.start:state.end].encode()).hexdigest()
                assert unchanged[state.key][digest]>0, ('Unrelated ownership changed',state.key)
                unchanged[state.key][digest]-=1
                continue
            assert state.key not in owners
            groups={}
            for region in regions:
                tag=region.scalar('country')[2:]
                assert tag not in groups
                groups[tag]=sorted(region.words('owned_provinces'))
                if tag in AFRICAN_TAGS|{'OPD'}:assert region.scalar('state_type')=='unincorporated'
                if tag=='HAW':assert region.scalar('state_type')=='incorporated'
            assert groups==wanted[state.key]['owners'], ('Incorrect partition',state.key)
            provinces=[p for ps in groups.values() for p in ps]
            assert len(provinces)==len(set(provinces))
            assert sorted(provinces)==wanted[state.key]['provinces']
            owners[state.key]=groups
    assert set(owners)==set(wanted)
    assert all(not +counts for counts in unchanged.values())
    assert not global_owners & set(baseline['retired'])
    for tag in AFRICAN_TAGS|{'OPD'}:
        assert definitions[tag].scalar('country_type')=='decentralized'
        assert tag in owners['s:'+definitions[tag].scalar('capital')]
        assert definitions[tag].words('cultures')
    for state,tags in owners.items():
        if state in baseline['africa_regions']:
            assert {t for t in tags if t in AFRICAN_TAGS}=={baseline['africa_regions'][state]},state
    for folder in ['pops','buildings']:
        seen=set()
        for path in (ROOT/'common/history'/folder).glob('*.txt'):
            for state in state_nodes(read(path)):
                if state.key not in wanted or folder not in wanted[state.key]:continue
                assert state.key not in seen, ('Duplicate history',folder,state.key)
                seen.add(state.key)
                for region in state.value:
                    if not region.key.startswith('region_state:'):continue
                    tag=region.key.split(':')[1]
                    assert tag in owners[state.key], ('Unowned history',folder,state.key,tag)
                    if folder=='pops':
                        for pop in region.children('create_pop'):
                            if tag in AFRICAN_TAGS:
                                assert pop.scalar('culture') in definitions[tag].words('cultures')
                actual=pop_totals(state) if folder=='pops' else building_signatures(state)
                assert json.loads(json.dumps(actual))==wanted[state.key][folder], ('History changed',folder,state.key)
        assert seen=={s for s,v in wanted.items() if folder in v}
    hawaii=owners['s:STATE_HAWAIIAN_ISLANDS']
    assert set(hawaii)=={'HAW'}
    vanilla=next(n for n in nodes(read(BASE/'map_data/state_regions/05_north_america.txt')) if n.key=='STATE_HAWAIIAN_ISLANDS')
    assert hawaii['HAW']==sorted(p.strip('"') for p in vanilla.words('provinces'))
    assert definitions['HAW'].scalar('country_type')=='unrecognized'
    assert definitions['HAW'].scalar('religion')=='animist'
    pacific_tags=set()
    for path in (ROOT/'common/history/states').glob('*.txt'):
        for state in state_nodes(read(path)):
            if state.key in baseline['pacific_states']:
                pacific_tags.update(n.scalar('country')[2:] for n in state.children('create_state'))
    assert {t for t in pacific_tags if definitions[t].scalar('country_type')=='decentralized'}=={'OPD'}
    assert {'HAW','PLY','OPD'}==pacific_tags
    loc=ROOT/'localization/english/replace/zzz_aoc_africa_pacific_l_english.yml'
    assert loc.read_bytes().startswith(b'\xef\xbb\xbf')
    for tag,name in NAMES.items():assert f' {tag}:0 "{name}"' in read(loc)
    history=nodes(read(ROOT/'common/history/countries/aoc_hawaii.txt'))[0]
    assert [n.key for n in history.value]==['c:HAW']
    laws='\n'.join(read(p) for p in (ROOT/'common/laws').glob('*.txt'))
    for law in history.value[0].children('activate_law'):
        assert re.search(r'^'+re.escape(law.value.split(':')[1])+r'\s*=',laws,re.M)
    print('PASS: three regional African decentralized owners; one Pacific decentralized owner; Hawaii owns every Hawaiian province and is centralized.')
    print('PASS: exact intended ownership; province, population and building conservation; valid capitals, cultures, histories, laws and names; all unrelated ownership unchanged.')

if __name__=='__main__':main()

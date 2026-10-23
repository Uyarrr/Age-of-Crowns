"""Check conservation, effective definitions and history for Africa/New Zealand."""
from collections import Counter
import hashlib
import json
import re
from setup_africa_nz_1444 import ROOT, PLAYABLE, NZ, nodes, state_nodes, read, pop_totals

def main():
    baseline = json.loads(read(ROOT/'docs/africa_nz_1444_baseline.json'))
    revision_path = ROOT/'docs/africa_pacific_regional_baseline.json'
    revision = json.loads(read(revision_path)) if revision_path.exists() else None
    revised_states = set(revision['states']) if revision else set()
    african_aggregates = {'AFD','AFC','AFE'} if revision else {'AFD'}
    wanted = baseline['states']
    definitions = {}
    for path in sorted((ROOT/'common/country_definitions').glob('*.txt')):
        text = read(path)
        for n in nodes(text):
            if re.match(r'\w+\s*\?=',text[n.start:n.end]) and n.key in definitions:
                continue
            definitions[n.key] = n
    owners, provinces, populations = {}, {}, Counter()
    untouched = {key:Counter(values) for key,values in baseline['untouched_states'].items()}
    for path in (ROOT/'common/history/states').glob('*.txt'):
        text = read(path)
        for state in state_nodes(text):
            if not state.children('create_state'):
                continue
            if state.key not in wanted:
                if state.key in revised_states:
                    continue  # Verified against the subsequent migration below.
                digest = hashlib.sha256(text[state.start:state.end].encode()).hexdigest()
                assert untouched[state.key][digest]>0, ('Unrelated state changed',state.key)
                untouched[state.key][digest]-=1
                continue
            assert state.key not in owners, ('Duplicate state',state.key)
            owners[state.key] = set()
            provinces[state.key] = []
            for region in state.children('create_state'):
                tag = region.scalar('country')[2:]
                assert tag not in owners[state.key]
                assert tag in definitions
                owners[state.key].add(tag)
                provinces[state.key] += region.words('owned_provinces')
                if tag in PLAYABLE or tag=='NPH':assert region.scalar('state_type')=='incorporated'
                if tag in african_aggregates|{'MZD'}:assert region.scalar('state_type')=='unincorporated'
            assert len(provinces[state.key])==len(set(provinces[state.key]))
            assert sorted(provinces[state.key])==wanted[state.key]['provinces'], state.key
    assert set(owners)==set(wanted)
    assert all(not +counts for key,counts in untouched.items() if key not in revised_states)
    pop_seen = set()
    for folder in ['pops','buildings']:
        for path in (ROOT/'common/history'/folder).glob('*.txt'):
            for state in state_nodes(read(path)):
                if state.key not in wanted:
                    continue
                for region in state.value:
                    if region.key.startswith('region_state:'):
                        tag=region.key.split(':')[1]
                        assert tag in owners[state.key], ('Unowned history',path,state.key,tag)
                        if folder=='pops':
                            populations[tag] += sum(int(p.scalar('size')) for p in region.children('create_pop'))
                if folder=='pops':
                    assert state.key not in pop_seen
                    pop_seen.add(state.key)
                    assert pop_totals(state)==wanted[state.key]['pops'], ('Pops changed',state.key)
    assert pop_seen=={s for s,data in wanted.items() if 'pops' in data}
    for tag in [*PLAYABLE,'NPH']:
        assert definitions[tag].scalar('country_type')=='unrecognized', tag
        assert tag in owners['s:'+definitions[tag].scalar('capital')], ('Unowned capital',tag)
        assert populations[tag]>0, ('Empty playable country',tag)
    for tag in [*african_aggregates,'MZD']:
        assert definitions[tag].scalar('country_type')=='decentralized'
        assert tag in owners['s:'+definitions[tag].scalar('capital')]
    african_tags={t for s,ts in owners.items() if s in baseline['africa_states'] for t in ts}
    assert {t for t in african_tags if definitions[t].scalar('country_type')=='decentralized'}==african_aggregates
    assert {t for s in NZ for t in owners[s]}=={'NPH','MZD'}
    assert len(provinces['s:STATE_NORTH_ISLAND'])>6
    assert sum(len(r.words('owned_provinces')) for p in (ROOT/'common/history/states').glob('*.txt') for s in state_nodes(read(p)) for r in s.children('create_state') if r.scalar('country')=='c:NPH')==6
    assert not set(baseline['retired']) & {t for ts in owners.values() for t in ts}
    history=nodes(read(ROOT/'common/history/countries/aoc_africa_nz.txt'))[0]
    assert {n.key[2:] for n in history.value}==set(PLAYABLE)|{'NPH'}
    laws='\n'.join(read(p) for p in (ROOT/'common/laws').glob('*.txt'))
    for n in history.value:
        for law in n.children('activate_law'):
            assert re.search(r'^'+re.escape(law.value.split(':')[1])+r'\s*=',laws,re.M)
    loc=ROOT/'localization/english/replace/zz_aoc_africa_nz_l_english.yml'
    assert loc.read_bytes().startswith(b'\xef\xbb\xbf')
    for tag in [*PLAYABLE,'AFD','NPH','MZD']:
        source = ROOT/'localization/english/replace/zzz_aoc_africa_pacific_l_english.yml' if revision and tag=='AFD' else loc
        assert re.search(r'^ '+tag+r':0 ',read(source),re.M)
        assert re.search(r'^ '+tag+r'_ADJ:0 ',read(source),re.M)
    assert ' PUE:0 "Pueblo"' in read(ROOT/'localization/english/replace/zz_aoc_north_america_l_english.yml')
    print(f'PASS: African owners {baseline["african_before"]} -> {len(african_tags)}; {len(PLAYABLE)} selected playable tags; {len(african_aggregates)} African decentralized owners.')
    print('PASS: Ngāpuhi owns six Northland provinces; all remaining New Zealand belongs to Māori Peoples.')
    print('PASS: province coverage, population and attributes, effective country types, owned capitals, history scopes, startup laws and names; all unrelated ownership states unchanged.')
    print('PASS: Pueblo renamed; new playable countries all have population.')
    if revision:
        from audit_africa_pacific import main as audit_revision
        audit_revision()

if __name__=='__main__':main()

"""Validate the 1444 Australian setup against its pre-migration baseline."""
from collections import Counter
import json
import re
from setup_australia_1444 import ROOT, STATES, FACTIONS, nodes, read

def main():
    baseline = json.loads(read(ROOT/'docs/australia_1444_baseline.json'))
    expected = set(FACTIONS) | {'AUP'}
    state_text = read(ROOT/'common/history/states/00_states.txt')
    states = {n.key:n for n in nodes(state_text)[0].value if n.key in baseline}
    owners, present = {}, set()
    for key,state in states.items():
        provinces = []
        owners[key] = set()
        for region in state.children('create_state'):
            tag = region.scalar('country')[2:]
            assert tag in expected, (key,tag)
            assert tag not in owners[key], (key,tag,'duplicate state')
            owners[key].add(tag)
            present.add(tag)
            provinces.extend(region.words('owned_provinces'))
            assert region.scalar('state_type') == ('incorporated' if tag in FACTIONS else 'unincorporated')
        assert len(provinces) == len(set(provinces)), (key,'duplicate province')
        assert sorted(provinces) == baseline[key]['provinces'], (key,'province coverage changed')
    assert present == expected
    counts = Counter()
    for state in nodes(read(ROOT/'common/history/pops/new_pops.txt'))[0].value:
        if state.key not in baseline:
            continue
        totals = Counter()
        for region in state.value:
            tag = region.key.split(':')[1]
            assert tag in owners[state.key], (state.key,tag,'pop has no owner')
            for pop in region.children('create_pop'):
                attrs = tuple((n.key,n.value) for n in pop.value if n.key != 'size')
                size = int(pop.scalar('size'))
                totals[attrs] += size
                counts[tag] += size
        assert [[[list(pair) for pair in a],count] for a,count in sorted(totals.items())] == baseline[state.key]['pops'], (state.key,'population changed')
    assert all(counts[t] > 0 for t in expected), counts
    definitions = nodes(read(ROOT/'common/country_definitions/aoc_australia.txt'))
    assert {n.key for n in definitions} == expected
    for n in definitions:
        assert n.scalar('country_type') == ('unrecognized' if n.key in FACTIONS else 'decentralized')
        assert n.scalar('religion') == 'animist'
        assert n.words('cultures') == ['aborigine']
        assert n.key in owners['s:'+n.scalar('capital')]
    for path in (ROOT/'common/country_definitions').glob('*.txt'):
        if path.name != 'aoc_australia.txt':
            assert not re.search(r'^(?:'+'|'.join(expected)+r')\s*\??=', read(path), re.M), path
    for state in nodes(read(ROOT/'common/history/buildings/13_australasia.txt'))[0].value:
        if state.key in baseline:
            assert {n.key.split(':')[1] for n in state.value} == owners[state.key]
    history = nodes(read(ROOT/'common/history/countries/aoc_australia.txt'))[0]
    assert {n.key[2:] for n in history.value} == set(FACTIONS)
    laws = '\n'.join(read(p) for p in (ROOT/'common/laws').glob('*.txt'))
    for nation in history.value:
        for law in nation.children('activate_law'):
            assert re.search(r'^'+re.escape(law.value.split(':')[1])+r'\s*=', laws, re.M), law.value
    loc = ROOT/'localization/english/replace/zz_aoc_australia_l_english.yml'
    assert loc.read_bytes().startswith(b'\xef\xbb\xbf')
    for tag in expected:
        assert re.search(r'^ '+tag+r':0 ', read(loc), re.M)
        assert re.search(r'^ '+tag+r'_ADJ:0 ', read(loc), re.M)
    print('PASS: seven playable nations; one decentralized remainder; all provinces, pop attributes and population totals preserved; capitals, buildings, laws, definitions and localization valid.')
    for tag in sorted(counts):
        print(f'{tag}: {counts[tag]:,} people')

if __name__ == '__main__':
    main()

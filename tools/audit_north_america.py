"""Validate the consolidated mainland setup against its pre-migration totals."""
from collections import Counter
import json
import re
from consolidate_north_america import FACTIONS, REGIONS, ROOT, parse, read


def main():
    baseline = json.loads(read(ROOT / 'docs/north_america_baseline.json'))
    wanted = set(baseline['provinces'])
    owners = {}
    active = set()
    for p in (ROOT / 'common/history/states').glob('*.txt'):
        # Resource-only supplements have no ownership, but still parse them.
        for top in parse(read(p)):
            if not isinstance(top.value, list): continue
            for s in top.value:
                if s.key not in wanted or not s.children('create_state'): continue
                assert s.key not in owners, ('duplicate state declaration', p, s.key)
                entries = s.children('create_state')
                tags = [n.scalar('country').removeprefix('c:') for n in entries]
                assert len(tags) == len(set(tags)), ('duplicate state owner', s.key)
                assert not (len(tags) == 1 and tags[0] in FACTIONS), ('playable faction owns a full state', s.key, tags[0])
                provinces = [v for n in entries for v in n.words('owned_provinces')]
                assert len(provinces) == len(set(provinces)), ('overlapping provinces', s.key)
                assert sorted(provinces) == baseline['provinces'][s.key], ('changed province coverage', s.key)
                for n in entries:
                    tag = n.scalar('country')[2:]
                    if tag in FACTIONS: assert n.scalar('state_type') == 'incorporated'
                owners[s.key] = set(tags)
                active.update(tags)
    assert set(owners) == wanted
    assert active == set(FACTIONS) | set(REGIONS), active
    definitions = {}
    for p in (ROOT / 'common/country_definitions').glob('*.txt'):
        source = read(p)
        for tag in active | {'IRC'}:
            matches = list(re.finditer(r'(?m)^' + tag + r'\s*\??=\s*\{', source))
            if matches:
                assert len(matches) == 1 and tag not in definitions, ('duplicate country definition', tag)
                definitions[tag] = p
    assert set(definitions) == active | {'IRC'}
    cultures = set()
    for p in (ROOT / 'common/cultures').glob('*.txt'):
        cultures.update(re.findall(r'(?m)^([a-z_]+)\s*=\s*\{', read(p)))
    for n in parse(read(ROOT / 'common/country_definitions/aoc_north_america.txt')):
        if n.key == 'IRC': continue
        expected = 'unrecognized' if n.key in FACTIONS else 'decentralized'
        assert n.scalar('country_type') == expected, n.key
        assert n.key in owners['s:' + n.scalar('capital')], ('unowned capital', n.key)
        assert set(n.words('cultures')) <= cultures, ('undefined culture', n.key)
    manifest_path = ROOT / 'docs/north_america_1444_provinces.json'
    if manifest_path.exists():
        manifest = json.loads(read(manifest_path))
        profiles = json.loads(read(ROOT / 'tools/north_america_1444_homelands.json'))['factions']
        assert set(profiles) == set(FACTIONS)
        assert {'s:' + s for s in manifest['states']} == wanted
        for p in (ROOT / 'common/history/states').glob('*.txt'):
            for top in parse(read(p)):
                if not isinstance(top.value, list): continue
                for state in top.value:
                    if state.key not in wanted or not state.children('create_state'): continue
                    actual = {n.scalar('country')[2:]: sorted(n.words('owned_provinces')) for n in state.children('create_state')}
                    assert actual == manifest['states'][state.key.removeprefix('s:')], ('research province list mismatch', state.key)
                    for tag in actual:
                        if tag in profiles:
                            assert state.key.removeprefix('s:STATE_') in profiles[tag]['states'].split(), ('outside researched region', state.key, tag)
                            assert profiles[tag]['sources'] and profiles[tag]['confidence']
        for n in parse(read(ROOT / 'common/country_definitions/aoc_north_america.txt')):
            if n.key in profiles:
                assert n.scalar('capital') == 'STATE_' + profiles[n.key]['capital'], ('wrong researched capital', n.key)
    population = Counter()
    for folder in ('pops', 'buildings'):
        for p in (ROOT / 'common/history' / folder).glob('*.txt'):
            for top in parse(read(p)):
                if not isinstance(top.value, list): continue
                for state in top.value:
                    if state.key not in wanted: continue
                    seen = set()
                    for region in state.value:
                        tag = region.key.removeprefix('region_state:')
                        assert tag in owners[state.key], ('orphan history scope', p, state.key, tag)
                        assert tag not in seen, ('duplicate history scope', p, state.key, tag)
                        seen.add(tag)
                        if folder == 'pops':
                            for pop in region.children('create_pop'):
                                identity = (state.key, pop.scalar('culture'), pop.scalar('religion'), pop.scalar('pop_type'))
                                population[identity] += int(pop.scalar('size'))
    expected = Counter({tuple(row['identity']): row['size'] for row in baseline['population']})
    assert population == expected, 'Population changed by state/culture/religion/type'
    history = parse(read(ROOT / 'common/history/countries/aoc_north_america.txt'))[0]
    assert {n.key.removeprefix('c:') for n in history.value} == set(FACTIONS)
    laws = set()
    for p in (ROOT / 'common/laws').glob('*.txt'):
        laws.update(re.findall(r'(?m)^(law_\w+)\s*=\s*\{', read(p)))
    for country in history.value:
        for law in country.children('activate_law'):
            assert law.value.removeprefix('law_type:') in laws, ('undefined startup law', country.key, law.value)
    localized = {}
    north_america_loc = ROOT / 'localization/english/replace/zz_aoc_north_america_l_english.yml'
    assert north_america_loc.read_bytes().startswith(b'\xef\xbb\xbfl_english:\n'), 'North America localization needs a UTF-8 BOM and l_english header'
    for p in (ROOT / 'localization/english').rglob('*.yml'):
        source = read(p)
        # Entries in a file with no language header are not loaded by the game.
        if not re.search(r'^l_english:\s*$', source, re.M): continue
        localized.update(re.findall(r'^\s*(\w+):(?:\d+)?\s*"([^"\n]*)"', source, re.M))
    for tag, data in {**FACTIONS, **REGIONS}.items():
        assert localized.get(tag) == data[0], ('incorrect country name', tag)
        assert localized.get(tag + '_ADJ') == data[1], ('incorrect adjective', tag)
    assert localized.get('IRC') == 'Iron Confederacy'
    assert localized.get('IRC_ADJ') == 'Cree-Assiniboine'
    # The historical alliance is a dormant, higher-tier formable; the Cree
    # starting state has an independent tag and flag instead of borrowing IRC.
    assert 'CRY' in active and 'IRC' not in active
    country_defs = {n.key: n for n in parse(read(ROOT / 'common/country_definitions/aoc_north_america.txt'))}
    assert country_defs['CRY'].words('cultures') == ['cree']
    assert country_defs['IRC'].scalar('country_type') == 'unrecognized'
    assert country_defs['IRC'].scalar('tier') == 'kingdom'
    assert country_defs['IRC'].words('cultures') == ['cree', 'siouan', 'algonquian']
    formations = {}
    for p in (ROOT / 'common/country_formation').glob('*.txt'):
        for n in parse(read(p).replace('?=', ' =')):
            if n.key == 'IRC':
                assert 'IRC' not in formations, 'Duplicate IRC formable'
                formations['IRC'] = n
    formation = formations['IRC']
    assert formation.words('states') == ['STATE_ALBERTA', 'STATE_SASKATCHEWAN', 'STATE_MANITOBA']
    assert float(formation.scalar('required_states_fraction')) == 0.66
    founders = formation.child('potential').child('custom_tooltip').child('OR')
    assert {n.key for n in founders.value} == {'c:CRY', 'c:OJB'}
    assert all(n.value == 'this' for n in founders.value)
    possible = formation.child('possible')
    assert {n.value for n in possible.children('has_technology_researched')} == {'nation_formation', 'iron_weapons'}
    assert possible.scalar('is_at_war') == 'no' and possible.scalar('is_subject') == 'no'
    assert any(n.scalar('exists') == 'c:IRC' for n in possible.children('NOT'))
    assert any(n.scalar('is_country_type') == 'decentralized' for n in possible.children('NOT'))
    for p in (ROOT / 'common/history').rglob('*.txt'):
        assert not re.search(r'\b(?:c:|region_state:)IRC\b', read(p)), ('Iron Confederacy has startup history', p)
    coats = parse(read(ROOT / 'common/coat_of_arms/coat_of_arms/aoc_north_america.txt'))
    assert any(n.key == 'CRY' for n in coats), 'Cree needs its own banner'
    active_global = set()
    for p in (ROOT / 'common/history/states').glob('*.txt'):
        for top in parse(read(p)):
            if not isinstance(top.value, list): continue
            for state in top.value:
                if isinstance(state.value, list):
                    active_global.update(n.scalar('country')[2:] for n in state.children('create_state'))
    retired = set(baseline['old_active_tags']) - active_global
    diplomacy = parse(read(ROOT / 'common/history/diplomacy/00_relations.txt').replace('?=', ' ='))[0]
    for country in diplomacy.value:
        assert country.key.startswith('c:') and isinstance(country.value, list), ('invalid country scope', country.key)
        assert country.key[2:] not in retired
        for relation in country.children('set_relations'):
            assert relation.scalar('country', '')[2:] not in retired
    print(f'PASS: {len(FACTIONS)} playable, {len(REGIONS)} decentralized, {len(owners)} states.')
    print(f'PASS: {sum(len(p) for p in baseline["provinces"].values())} provinces; {sum(population.values())} population preserved.')
    print('PASS: unique definitions, owned capitals, cultures, incorporated playable states, and pop/building scopes.')
    print('PASS: startup laws, English country names, and retired-country diplomacy cleanup.')
    print('PASS: independent Cree tag and banner; dormant Iron Confederacy formable, founders, regions and technology requirements.')
    if manifest_path.exists(): print('PASS: explicit researched province lists, allowed homeland regions, and revised capitals.')


if __name__ == '__main__': main()

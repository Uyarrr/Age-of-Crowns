/** One-time 1.15 map migration. Review docs/map_1_15_migration.json afterward.
 * node tools/migrate_map_1_15.cjs --apply
 * Province identities retain their 1444 owner across vanilla state boundaries.
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { audit, parse, children, scalar, words, canonical, read, files, root, base } = require('./audit_map_ownership.cjs');
const manifestPath = path.join(root, 'docs/map_1_15_migration.json');
const renamed = { STATE_KAUNAS: 'STATE_LITHUANIA', STATE_TARTARIA: 'STATE_SARATOV', STATE_GALICH: 'STATE_VOLOGDA', STATE_CHUKOTKA: 'STATE_KAMCHATKA' };
const write = (p, text) => {
  const bom = fs.existsSync(p) && fs.readFileSync(p).subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf]));
  fs.writeFileSync(p, (bom ? '\uFEFF' : '') + text);
};
const raw = (text, n) => text.slice(n.start, n.end);
const replace = (text, edits) => edits.sort((a, b) => b.start - a.start).reduce((t, e) => t.slice(0, e.start) + e.text + t.slice(e.end), text);
const increment = (map, key, amount = 1) => map.set(key, (map.get(key) || 0) + amount);

function allocate(total, weights) {
  const sum = [...weights.values()].reduce((a, b) => a + b, 0);
  const rows = [...weights].map(([key, weight]) => ({ key, amount: Math.floor(total * weight / sum), remainder: total * weight % sum }));
  let left = total - rows.reduce((n, r) => n + r.amount, 0);
  rows.sort((a, b) => b.remainder - a.remainder || a.key.localeCompare(b.key));
  for (let i = 0; i < left; i++) rows[i].amount++;
  return new Map(rows.map(r => [r.key, r.amount]));
}

function historyTotals(folder) {
  const totals = new Map();
  for (const p of files(path.join(root, 'common/history', folder))) {
    const text = read(p);
    for (const top of parse(text)) for (const state of top.value || []) for (const region of state.value || []) {
      for (const n of children(region, folder === 'pops' ? 'create_pop' : 'create_building')) {
        const key = folder === 'pops'
          ? JSON.stringify([scalar(n, 'culture'), scalar(n, 'religion'), scalar(n, 'pop_type')])
          : raw(text, n).replace(/\s+/g, '');
        increment(totals, key, folder === 'pops' ? Number(scalar(n, 'size')) : 1);
      }
    }
  }
  return Object.fromEntries([...totals].sort(([a], [b]) => a.localeCompare(b)));
}

function main() {
  assert(process.argv.includes('--apply'), 'Pass --apply for this one-time migration.');
  assert(!fs.existsSync(manifestPath), 'Migration already applied; run audit_map_ownership.cjs.');
  const before = audit();
  assert.deepEqual([...before.obsoleteStates].sort(), Object.keys(renamed).sort(), 'Unexpected source map');
  const beforePops = historyTotals('pops');
  const beforeBuildings = historyTotals('buildings');
  const regions = new Map(files(path.join(base, 'map_data/state_regions')).flatMap(p => parse(read(p))).filter(n => scalar(n, 'subsistence_building')).map(n => [n.key, n]));
  const target = new Map([...regions].flatMap(([s, n]) => words(n, 'provinces').map(p => [canonical(p), s])));
  const stateFiles = files(path.join(root, 'common/history/states')).map(p => ({ p, text: read(p) }));
  const sources = [];
  const candidates = new Map();
  for (const file of stateFiles) for (const top of parse(file.text)) for (const state of top.value || []) {
    if (!children(state, 'create_state').length) continue;
    const source = { file, state, name: state.key.slice(2) };
    sources.push(source);
    for (const region of children(state, 'create_state')) for (const province of words(region, 'owned_provinces')) {
      const code = canonical(province);
      if (!candidates.has(code)) candidates.set(code, []);
      candidates.get(code).push({ source, region, owner: scalar(region, 'country'), province });
    }
  }
  const chosen = new Map();
  const corrections = [];
  for (const [code, options] of candidates) {
    assert(target.has(code), `Removed province requires manual handling: ${code}`);
    // Dedicated regional history supersedes converter leftovers. Within the
    // regional files, the smaller explicit enclave wins over a broad list.
    options.sort((a, b) => Number(path.basename(a.source.file.p) === '00_states.txt') - Number(path.basename(b.source.file.p) === '00_states.txt')
      || Number(a.source.name !== target.get(code)) - Number(b.source.name !== target.get(code))
      || words(a.region, 'owned_provinces').length - words(b.region, 'owned_provinces').length);
    const winner = options[0];
    chosen.set(code, winner);
    if (options.length > 1) corrections.push({ province: winner.province, state: target.get(code), owner: winner.owner, removed: options.slice(1).map(c => ({ state: c.source.name, owner: c.owner })) });
  }
  const newProvinces = [...target.keys()].filter(p => !chosen.has(p));
  assert.deepEqual(newProvinces, ['XEF50C0'], 'Unexpected new province requires an explicit owner');
  const pacific = sources.find(s => s.name === 'STATE_WEST_MICRONESIA');
  const pacificRegion = children(pacific.state, 'create_state').find(c => scalar(c, 'country') === 'c:OPD');
  assert(pacificRegion, 'Missing established Micronesian regional owner');
  chosen.set('XEF50C0', { source: pacific, region: pacificRegion, owner: 'c:OPD', province: 'xEF50C0' });

  const affected = new Set(before.issues.map(i => i.state).concat(before.obsoleteStates));
  for (const [code, c] of chosen) if (c.source.name !== target.get(code)) { affected.add(c.source.name); affected.add(target.get(code)); }
  const groups = new Map();
  for (const [code, c] of chosen) {
    const state = target.get(code);
    if (!groups.has(state)) groups.set(state, new Map());
    const owners = groups.get(state);
    if (!owners.has(c.owner)) owners.set(c.owner, []);
    owners.get(c.owner).push(c);
  }
  // Where did each old country's territory go? This also repairs history for
  // converter owners overridden by the dedicated South American setup.
  const historyMap = new Map();
  const stateMap = new Map();
  for (const s of sources) {
    const destinations = new Map();
    for (const region of children(s.state, 'create_state')) {
      const weights = new Map();
      for (const province of words(region, 'owned_provinces')) {
        const code = canonical(province);
        const dest = target.get(code);
        const winner = chosen.get(code);
        increment(weights, `${dest}|${winner.owner.slice(2)}`);
        increment(destinations, dest);
      }
      historyMap.set(`${s.name}|${scalar(region, 'country').slice(2)}`, weights);
    }
    if (!stateMap.has(s.name)) stateMap.set(s.name, new Map());
    for (const [dest, weight] of destinations) increment(stateMap.get(s.name), dest, weight);
  }

  const archivedStates = parse(read(path.join(root, 'common/history/states/99_converter_states.zzz')))[0].value;
  const orphanRepairs = [];
  for (const folder of ['pops', 'buildings']) for (const p of files(path.join(root, 'common/history', folder))) {
    for (const top of parse(read(p))) for (const state of top.value || []) {
      const old = state.key.replace(/^s:/, '');
      if (!affected.has(old)) continue;
      for (const region of state.value || []) {
        if (!region.value.length) continue;
        const owner = region.key.slice('region_state:'.length);
        if (historyMap.has(`${old}|${owner}`)) continue;
        const archive = archivedStates.find(s => s.key === state.key);
        const oldRegions = archive ? children(archive, 'create_state').filter(c => scalar(c, 'country') === `c:${owner}`) : [];
        const weights = new Map();
        const provinces = oldRegions.flatMap(c => words(c, 'owned_provinces'));
        if (provinces.length) {
          for (const province of provinces) {
            const code = canonical(province);
            increment(weights, `${target.get(code)}|${chosen.get(code).owner.slice(2)}`);
          }
        } else {
          // No surviving province list for these two legacy population scopes.
          // Keep their population in its original geographical state, divided
          // between that state's intended owners by province count.
          for (const s of sources.filter(s => s.name === old)) for (const c of children(s.state, 'create_state')) for (const province of words(c, 'owned_provinces')) {
            const code = canonical(province);
            increment(weights, `${target.get(code)}|${chosen.get(code).owner.slice(2)}`);
          }
        }
        assert(weights.size, `Cannot recover history for ${old} ${owner}`);
        historyMap.set(`${old}|${owner}`, weights);
        orphanRepairs.push({ state: old, owner, method: provinces.length ? 'archived converter province list' : 'same-state province proportions', destinations: Object.fromEntries(weights) });
      }
    }
  }

  // Rebuild only affected ownership blocks; unrelated state text stays intact.
  const output = [];
  for (const state of [...affected].filter(s => regions.has(s)).sort()) {
    const parts = [`\ts:${state} = {`];
    for (const [owner, entries] of [...groups.get(state)].sort(([a], [b]) => a.localeCompare(b))) {
      const exemplar = entries.find(c => c.source.name === state) || entries[0];
      const attrs = exemplar.region.value.filter(n => !['country', 'owned_provinces'].includes(n.key));
      parts.push('\t\tcreate_state = {', `\t\t\tcountry = ${owner}`, `\t\t\towned_provinces = { ${entries.map(c => c.province).sort().join(' ')} }`);
      for (const attr of attrs) parts.push('\t\t\t' + raw(exemplar.source.file.text, attr));
      parts.push('\t\t}');
    }
    const metadata = new Set();
    for (const source of sources) if (stateMap.get(source.name)?.has(state)) {
      for (const n of source.state.value.filter(n => n.key !== 'create_state')) metadata.add(raw(source.file.text, n));
    }
    for (const entry of metadata) parts.push('\t\t' + entry);
    parts.push('\t}');
    output.push(parts.join('\n'));
  }
  for (const file of stateFiles) {
    const edits = sources.filter(s => s.file === file && affected.has(s.name)).map(s => ({ start: s.state.start, end: s.state.end, text: '' }));
    if (edits.length) write(file.p, replace(file.text, edits));
  }
  write(path.join(root, 'common/history/states/aoc_states_map_1_15.txt'), '# Victoria 3 1.15: retain 1444 province owners across the revised state boundaries.\nSTATES = {\n' + output.join('\n\n') + '\n}\n');

  for (const folder of ['pops', 'buildings']) {
    const buckets = new Map();
    for (const p of files(path.join(root, 'common/history', folder))) {
      const text = read(p);
      const edits = [];
      for (const top of parse(text)) for (const state of top.value || []) {
        const old = state.key.replace(/^s:/, '');
        if (!affected.has(old)) continue;
        edits.push({ start: state.start, end: state.end, text: '' });
        for (const region of state.value || []) {
          assert(region.key.startsWith('region_state:'), `Unexpected history scope: ${region.key}`);
          const owner = region.key.slice('region_state:'.length);
          const weights = historyMap.get(`${old}|${owner}`);
          // Existing empty orphan scopes carry no history to migrate.
          if (!region.value.length) continue;
          assert(weights?.size, `Nonempty history has no territory: ${folder} ${old} ${owner}`);
          for (const n of region.value) {
            if (folder === 'pops') {
              assert.equal(n.key, 'create_pop');
              const size = children(n, 'size')[0];
              assert(size && Number.isInteger(Number(size.value)));
              for (const [dest, amount] of allocate(Number(size.value), weights)) {
                if (!amount) continue;
                const value = replace(raw(text, n), [{ start: size.start - n.start, end: size.end - n.start, text: `size = ${amount}` }]);
                if (!buckets.has(dest)) buckets.set(dest, []);
                buckets.get(dest).push(value);
              }
            } else {
              // Buildings are indivisible: place each original block once in
              // the largest successor region of the same country.
              const dest = [...weights].sort(([a, aw], [b, bw]) => bw - aw || a.localeCompare(b))[0][0];
              if (!buckets.has(dest)) buckets.set(dest, []);
              let value = raw(text, n);
              const newOwner = dest.split('|')[1];
              if (newOwner !== owner) value = value.replace(new RegExp(`\\bc:${owner}\\b`, 'g'), `c:${newOwner}`);
              buckets.get(dest).push(value);
            }
          }
        }
      }
      if (edits.length) write(p, replace(text, edits));
    }
    const states = new Map();
    for (const [dest, values] of [...buckets].sort(([a], [b]) => a.localeCompare(b))) {
      const [state, owner] = dest.split('|');
      if (!states.has(state)) states.set(state, []);
      states.get(state).push(`\t\tregion_state:${owner} = {\n${values.map(v => '\t\t\t' + v).join('\n')}\n\t\t}`);
    }
    write(path.join(root, `common/history/${folder}/aoc_map_1_15.txt`), `${folder.toUpperCase()} = {\n${[...states].map(([state, rs]) => `\ts:${state} = {\n${rs.join('\n')}\n\t}`).join('\n')}\n}\n`);
  }

  // Transfer custom resource history as well. Sum merged capped potentials;
  // split a retired state's quantities using its province-count proportions.
  for (const filename of ['aoc_states_resource_potential.txt', 'aoc_states_agricultural_potential.txt']) {
    const p = path.join(root, 'common/history/states', filename);
    const text = read(p);
    const edits = [], resources = new Map(), agriculture = new Map();
    for (const top of parse(text)) for (const state of top.value || []) {
      const old = state.key.slice(2);
      if (!affected.has(old)) continue;
      edits.push({ start: state.start, end: state.end, text: '' });
      const weights = stateMap.get(old);
      assert(weights?.size, `No resource migration for ${old}`);
      for (const n of state.value) {
        if (n.key === 'change_resource_potential') {
          for (const [dest, amount] of allocate(Number(scalar(n, 'amount')), weights)) {
            if (amount) increment(resources, `${dest}|${scalar(n, 'type')}`, amount);
          }
        } else {
          assert.equal(n.key, 'add_resource_potential');
          for (const dest of weights.keys()) agriculture.set(`${dest}|${n.value}`, true);
        }
      }
    }
    const additions = new Map();
    for (const [key, amount] of resources) {
      const [state, type] = key.split('|');
      if (!additions.has(state)) additions.set(state, []);
      additions.get(state).push(`change_resource_potential = { type = ${type} amount = ${amount} }`);
    }
    for (const key of agriculture.keys()) {
      const [state, type] = key.split('|');
      if (!additions.has(state)) additions.set(state, []);
      additions.get(state).push(`add_resource_potential = ${type}`);
    }
    const close = text.lastIndexOf('}');
    edits.push({ start: close, end: close, text: '\n    # Potentials transferred to the 1.15 state boundaries.\n' + [...additions].sort(([a], [b]) => a.localeCompare(b)).map(([state, values]) => `    s:${state} = {\n${values.map(v => '        ' + v).join('\n')}\n    }`).join('\n') + '\n' });
    write(p, replace(text, edits));
  }

  // Retired state identifiers must also leave capitals and formation rules.
  for (const folder of ['country_definitions', 'country_formation', 'country_creation']) for (const p of files(path.join(root, 'common', folder))) {
    const original = read(p);
    let updated = original.replace(/\bSTATE_(?:KAUNAS|TARTARIA|GALICH|CHUKOTKA)\b/g, s => renamed[s]);
    const deduplicate = [];
    for (const country of parse(updated)) for (const states of children(country, 'states')) {
      const seen = new Set();
      for (const state of states.value) {
        if (seen.has(state.key)) deduplicate.push({ start: state.start, end: state.end, text: '' });
        seen.add(state.key);
      }
    }
    updated = replace(updated, deduplicate);
    if (updated !== original) write(p, updated);
  }
  const after = audit();
  assert.equal(after.issues.length, 0, JSON.stringify(after.issues));
  assert.equal(after.obsoleteStates.length, 0);
  assert.deepEqual(historyTotals('pops'), beforePops, 'Population identity totals changed');
  const afterBuildings = historyTotals('buildings');
  // Owner corrections intentionally change the ownership field of buildings;
  // compare structure with country tags normalized, retaining every block.
  const normalizeBuildings = data => {
    const totals = new Map();
    for (const [key, count] of Object.entries(data)) increment(totals, key.replace(/c:[A-Za-z0-9_]+/g, 'c:OWNER'), count);
    return Object.fromEntries([...totals].sort(([a], [b]) => a.localeCompare(b)));
  };
  assert.deepEqual(normalizeBuildings(afterBuildings), normalizeBuildings(beforeBuildings), 'Building configuration totals changed');
  const transfers = [];
  for (const [code, c] of chosen) if (c.source.name !== target.get(code)) transfers.push({ province: c.province, from: c.source.name, to: target.get(code), owner: c.owner });
  const finalOwners = Object.fromEntries([...groups].filter(([s]) => affected.has(s)).sort(([a], [b]) => a.localeCompare(b)).map(([state, owners]) => [state, Object.fromEntries([...owners].map(([owner, entries]) => [owner, entries.map(c => canonical(c.province)).sort()]))]));
  write(manifestPath, JSON.stringify({ gameVersion: '1.15.0', renamed, before, after, newProvinces: [{ province: 'xEF50C0', state: 'STATE_WEST_MICRONESIA', owner: 'c:OPD' }], corrections, transfers, orphanRepairs, finalOwners, populationTotals: beforePops, buildingTotals: afterBuildings }, null, 2) + '\n');
  console.log(`Migrated ${transfers.length} province assignments; resolved ${corrections.length} overlaps; assigned one new island.`);
  console.log('PASS: complete land coverage, population conservation and building conservation.');
}
if (require.main === module) main();
module.exports = { historyTotals };

/** Regression checks for the 1.15 ownership and startup-history migration. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { audit, parse, children, scalar, words, canonical, read, files, root } = require('./audit_map_ownership.cjs');
const { historyTotals } = require('./migrate_map_1_15.cjs');
const manifest = JSON.parse(read(path.join(root, 'docs/map_1_15_migration.json')));
const result = audit();
assert.equal(result.issues.length, 0, JSON.stringify(result.issues));
assert.deepEqual(result.obsoleteStates, []);
const actual = {};
const owners = new Map();
for (const p of files(path.join(root, 'common/history/states'))) {
  for (const top of parse(read(p))) for (const s of top.value || []) {
    const state = s.key.slice(2);
    for (const c of children(s, 'create_state')) {
      const owner = scalar(c, 'country');
      if (!owners.has(state)) owners.set(state, new Set());
      owners.get(state).add(owner.slice(2));
      if (!(state in manifest.finalOwners)) continue;
      actual[state] ??= {};
      assert(!(owner in actual[state]), `Repeated create_state for ${state} ${owner}`);
      actual[state][owner] = words(c, 'owned_provinces').map(canonical).sort();
    }
  }
}
assert.deepEqual(actual, manifest.finalOwners, '1444 ownership drifted from reviewed migration');
for (const folder of ['pops', 'buildings']) {
  for (const p of files(path.join(root, 'common/history', folder))) {
    for (const top of parse(read(p))) for (const state of top.value || []) {
      if (!(state.key.slice(2) in manifest.finalOwners)) continue;
      for (const region of state.value || []) {
        assert(region.key.startsWith('region_state:'), `Invalid scope in ${p}: ${region.key}`);
        if (!region.value.length) continue;
        assert(owners.get(state.key.slice(2))?.has(region.key.slice('region_state:'.length)), `Orphan ${folder}: ${state.key} ${region.key}`);
      }
    }
  }
}
assert.deepEqual(historyTotals('pops'), manifest.populationTotals, 'Population totals changed');
assert.deepEqual(historyTotals('buildings'), manifest.buildingTotals, 'Building configurations changed');
for (const filename of ['aoc_states_resource_potential.txt', 'aoc_states_agricultural_potential.txt']) {
  const seen = new Set();
  for (const top of parse(read(path.join(root, 'common/history/states', filename)))) for (const state of top.value || []) {
    if (!(state.key.slice(2) in manifest.finalOwners)) continue;
    for (const n of state.value) {
      const type = n.key === 'change_resource_potential' ? scalar(n, 'type') : n.value;
      const key = `${state.key}|${type}`;
      assert(!seen.has(key), `Repeated resource history: ${key}`);
      seen.add(key);
      if (n.key === 'change_resource_potential') assert(Number.isInteger(Number(scalar(n, 'amount'))) && Number(scalar(n, 'amount')) > 0);
    }
  }
}
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}
const retired = new RegExp(`\\b(?:${Object.keys(manifest.renamed).join('|')})\\b`);
for (const p of walk(path.join(root, 'common')).filter(p => p.endsWith('.txt'))) assert(!retired.test(read(p)), `Retired state reference: ${p}`);
const definitions = new Map();
for (const p of files(path.join(root, 'common/country_definitions'))) {
  const text = read(p);
  for (const n of parse(text)) {
    if (!/^\w+\s*\?=/.test(text.slice(n.start, n.end)) || !definitions.has(n.key)) definitions.set(n.key, n);
  }
}
for (const tags of owners.values()) for (const tag of tags) assert(definitions.has(tag), `Undefined province owner: ${tag}`);
for (const tag of ['LIT', 'C17', 'PRM']) {
  const capital = scalar(definitions.get(tag), 'capital');
  assert(owners.get(capital)?.has(tag), `Unowned migrated capital: ${tag} ${capital}`);
}
for (const folder of ['country_creation', 'country_formation']) for (const p of files(path.join(root, 'common', folder))) {
  for (const n of parse(read(p))) for (const states of children(n, 'states')) {
    const list = states.value.map(s => s.key);
    assert.equal(new Set(list).size, list.length, `Repeated formation/release state: ${p} ${n.key}`);
  }
}
console.log(`PASS: ${result.landStates} land states, ${result.assignedProvinces} provinces, unique complete coverage.`);
console.log(`PASS: exact 1444 ownership in ${Object.keys(actual).length} migrated states; valid owners and migrated capitals.`);
console.log(`PASS: ${Object.values(manifest.populationTotals).reduce((a, b) => a + b, 0)} population and ${Object.values(manifest.buildingTotals).reduce((a, b) => a + b, 0)} building blocks preserved.`);
console.log('PASS: migrated population/building scopes, resource history, formation/release lists, and no retired state references.');

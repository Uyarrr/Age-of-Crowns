/** Check the deliberately restricted 1444 crop map and resource accounting. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { parse, children, scalar, words, files, read, root } = require('./audit_map_ownership.cjs');
const map = new Map();
let known = 0, hidden = 0;
const forbidden = new Set(['building_whaling_station', 'building_oil_rig', 'building_rubber_plantation', 'building_opium_plantation', 'building_tea_plantation', 'building_banana_plantation', 'building_silk_plantation']);
const coffee = new Set(['STATE_YEMEN', 'STATE_OROMIA', 'STATE_AMHARA']);
for (const p of files(path.join(root, 'map_data/state_regions'))) {
  const region = Number(path.basename(p).slice(0, 2));
  for (const s of parse(read(p))) {
    if (!scalar(s, 'subsistence_building')) continue;
    const arable = words(s, 'arable_resources');
    const allowed = new Set(arable);
    const caps = children(s, 'capped_resources');
    for (const c of caps) for (const n of c.value) allowed.add(n.key);
    const seen = new Set();
    for (const r of children(s, 'resource')) {
      const type = scalar(r, 'type').replaceAll('"', '');
      assert(!seen.has(type), `${s.key}: duplicate ${type}`);
      seen.add(type); allowed.add(type);
      const a = Number(scalar(r, 'amount')), b = Number(scalar(r, 'undiscovered_amount'));
      assert(Number.isInteger(a) && Number.isInteger(b) && a >= 0 && b >= 0 && Math.abs(a - b) <= 1, `${s.key}: invalid split for ${type}`);
      known += a; hidden += b;
    }
    for (const type of allowed) assert(!forbidden.has(type), `${s.key}: ${type}`);
    if (arable.includes('building_coffee_plantation')) assert(coffee.has(s.key), `${s.key}: coffee`);
    const americas = region >= 5 && region <= 7 && !['STATE_HAWAIIAN_ISLANDS', 'STATE_BERMUDA'].includes(s.key);
    for (const crop of ['building_maize_farm', 'building_tobacco_plantation', 'building_cocoa_plantation', 'building_chili_plantation']) {
      if (arable.includes(crop)) assert(americas, `${s.key}: ${crop}`);
    }
    if (arable.includes('building_tea_garden')) assert(region === 11, `${s.key}: tea`);
    if (arable.includes('building_clove_grove')) assert.equal(s.key, 'STATE_MOLUCCAS');
    map.set(s.key, allowed);
  }
}
assert(Math.abs(known - hidden) <= 1, 'Global discovery split');
const buildings = new Set();
for (const name of ['uyr_agro.txt', 'uyr_plantation.txt', 'uyr_mines.txt']) {
  for (const n of parse(read(path.join(root, 'common/buildings', name)))) if (n.key.startsWith('building_')) buildings.add(n.key);
}
for (const p of files(path.join(root, 'common/history/buildings'))) for (const top of parse(read(p))) for (const state of top.value || []) {
  for (const region of state.value || []) for (const b of children(region, 'create_building')) {
    const type = (scalar(b, 'building') || '').replaceAll('"', '');
    const potentials = map.get(state.key.slice(2));
    if (potentials && buildings.has(type)) assert(potentials.has(type), `${path.basename(p)}: ${state.key} lacks ${type}`);
  }
}
console.log(`PASS: ${map.size} states; ${known} available and ${hidden} undiscovered levels; restricted crops and starting buildings checked.`);

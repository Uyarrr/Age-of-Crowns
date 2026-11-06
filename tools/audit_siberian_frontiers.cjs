/** Verify the Siberian gate and that map overrides only change colonial traits. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { parse, children, scalar, words, read, files, root, base } = require('./audit_map_ownership.cjs');
const trait = 'state_trait_siberian_colonization';
const malaria = new Set(['state_trait_malaria', 'state_trait_severe_malaria']);
const expected = new Set(['TOMSK', 'TOBOLSK', 'UPPER_YENISEYSK', 'OB', 'KAMCHATKA', 'OKHOTSK', 'YAKUTSK', 'TRANS_BAIKAL', 'IRKUTSK', 'SURGUT', 'KRASNOYARSK', 'ALTAI', 'BURYATIA', 'KOLYMA', 'AMUR'].map(s => 'STATE_' + s));
const found = new Set();
let removed = 0;
// Combine repeated trait lists in the installed map before comparing semantics.
function normalized(nodes) {
  const result = [];
  const traits = [];
  for (const n of nodes) {
    if (n.key === 'traits') {
      traits.push(...n.value.map(v => v.key.replaceAll('"', '')).filter(v => !malaria.has(v) && v !== trait));
    } else result.push([n.key, Array.isArray(n.value) ? normalized(n.value) : n.value]);
  }
  if (traits.length) result.push(['traits', [...new Set(traits)].sort()]);
  return result;
}
const localMap = path.join(root, 'map_data/state_regions');
for (const p of files(path.join(base, 'map_data/state_regions'))) {
  const original = parse(read(p));
  const override = path.join(localMap, path.basename(p));
  const effective = fs.existsSync(override) ? parse(read(override)) : original;
  assert.deepEqual(normalized(effective), normalized(original), `Unrelated map change: ${p}`);
  for (const s of original) removed += children(s, 'traits').flatMap(t => t.value.map(v => v.key.replaceAll('"', ''))).filter(t => malaria.has(t)).length;
  for (const s of effective) {
    const traits = children(s, 'traits').flatMap(t => t.value.map(v => v.key.replaceAll('"', '')));
    assert(!traits.some(t => malaria.has(t)), `Malaria remains in ${s.key}`);
    if (traits.includes(trait)) {
      assert.equal(traits.filter(t => t === trait).length, 1);
      found.add(s.key);
    }
  }
}
assert.deepEqual(found, expected);
const definitions = parse(read(path.join(root, 'common/state_traits/colony_traits.txt')));
for (const key of malaria) {
  const def = definitions.find(n => n.key === 'REPLACE:' + key);
  assert(def);
  assert.equal(children(def, 'modifier')[0].value.length, 0);
  assert.equal(children(def, 'required_techs_for_colonization').length, 0);
}
const gate = definitions.find(n => n.key === trait);
assert.deepEqual(words(gate, 'required_techs_for_colonization'), ['siberian_frontiers']);
assert.deepEqual(words(gate, 'disabling_technologies'), ['siberian_frontiers']);
const technologies = files(path.join(root, 'common/technology/technologies')).flatMap(p => parse(read(p)));
const tech = technologies.filter(n => n.key === 'siberian_frontiers');
assert.equal(tech.length, 1);
assert.equal(scalar(tech[0], 'era'), 'era_5');
assert.equal(scalar(tech[0], 'category'), 'society');
for (const prerequisite of words(tech[0], 'unlocking_technologies')) assert(technologies.some(n => n.key === prerequisite));
for (const [node, field, size] of [[gate, 'icon', 150], [tech[0], 'texture', 256]]) {
  const p = path.join(root, scalar(node, field).replaceAll('"', ''));
  const dds = fs.readFileSync(p);
  assert.equal(dds.toString('ascii', 0, 4), 'DDS ');
  assert.equal(dds.readUInt32LE(12), size);
  assert.equal(dds.readUInt32LE(16), size);
}
const loc = fs.readFileSync(path.join(root, 'localization/english/aoc_siberian_frontiers_l_english.yml'));
assert.equal(loc.subarray(0, 3).toString('hex'), 'efbbbf');
for (const key of ['siberian_frontiers', 'siberian_frontiers_desc', trait, trait + '_desc']) assert(loc.toString('utf8').includes(' ' + key + ':0'));
console.log(`Verified ${found.size} gated Siberian states; ${removed} malaria assignments removed; map data preserved; Age 5 Society technology, localization, and both DDS icons valid.`);

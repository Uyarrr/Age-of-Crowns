/** Reject invalid law-variant triggers that caused recurring simulation errors.
 * Run: node tools/audit_performance.cjs
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const a = require('./audit_map_ownership.cjs');

function files(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry =>
    entry.isDirectory() ? files(path.join(dir, entry.name)) : [path.join(dir, entry.name)]);
}

const variants = new Map();
for (const file of a.files(path.join(a.root, 'common/laws'))) {
  for (const law of a.parse(a.read(file))) {
    const parent = Array.isArray(law.value) && law.value.find(n => n.key === 'parent');
    if (parent) variants.set(law.key, parent.value);
  }
}

const invalid = [];
let checks = 0;
for (const folder of ['common', 'events']) {
  for (const file of files(path.join(a.root, folder)).filter(p => p.endsWith('.txt'))) {
    // Strip comments while preserving line numbers and quoted strings.
    const text = a.read(file).replace(/"(?:\\.|[^"\\])*"|#[^\r\n]*/g,
      token => token.startsWith('#') ? '' : token);
    for (const match of text.matchAll(/\bhas_law_or_variant\s*=\s*law_type:(\w+)/g)) {
      checks++;
      if (variants.has(match[1])) {
        const line = text.slice(0, match.index).split('\n').length;
        invalid.push(`${path.relative(a.root, file)}:${line}: ${match[1]} is a variant of ${variants.get(match[1])}`);
      }
    }
  }
}
assert.equal(invalid.length, 0, invalid.join('\n'));

// Parse the affected files too, so malformed edits cannot pass the operand check.
for (const relative of [
  'common/political_movements/10_aoc_crown_and_estates_movements.txt',
  'common/political_movements/11_aoc_land_and_labour_movements.txt',
  'common/political_movements/12_aoc_commerce_movements.txt',
  'common/political_movement_pop_support/00_political_movement_pop_support.txt',
  'common/scripted_triggers/aoc_movement_triggers.txt',
]) a.parse(a.read(path.join(a.root, relative)));
console.log(`PASS: ${checks} law-family trigger operands checked against ${variants.size} local law variants; all five affected files parse.`);

const laws = new Set();
for (const file of a.files(path.join(a.root, 'common/laws'))) {
  for (const law of a.parse(a.read(file))) if (Array.isArray(law.value)) laws.add(law.key);
}
const treaty = a.read(path.join(a.root, 'common/treaty_articles/20_law_commitment.txt'));
a.parse(treaty);
for (const match of treaty.matchAll(/\blaw_type:(\w+)/g)) {
  assert(laws.has(match[1]), `Law commitment references absent law: ${match[1]}`);
}

const event = a.parse(a.read(path.join(a.root, 'events/uyr_events.txt')));
assert(event.some(n => n.key === 'uyr_events.1'), 'Colonization event must have a namespaced numeric ID');
for (const file of a.files(path.join(a.root, 'common/on_actions'))) {
  const text = a.read(file);
  a.parse(text);
  assert(!/^\s*colonization_rush\s*$/m.test(text), `Obsolete event ID in ${file}`);
}
console.log('PASS: law commitment references only existing laws; colonization event and on-actions parse with the corrected event ID.');

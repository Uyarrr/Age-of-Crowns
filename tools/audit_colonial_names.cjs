/** Static naming audit: node tools/audit_colonial_names.cjs [game directory] */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const game = process.argv[2] || 'C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game';
const read = file => fs.readFileSync(path.join(root, file), 'utf8').replace(/^\uFEFF/, '');
function parse(text) {
  const tokens = (text.match(/#[^\r\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>!?"#]+/g) || []).filter(t => !t.startsWith('#'));
  let i = 0;
  function block(nested = false) {
    const out = [];
    while (i < tokens.length && tokens[i] !== '}') {
      const key = tokens[i++];
      assert(!['{', '='].includes(key), `Unexpected ${key}`);
      let value;
      if (['=', '?=', '>=', '<=', '!=', '>', '<'].includes(tokens[i])) {
        i++;
        if (tokens[i] === '{') { i++; value = block(true); }
        else { value = tokens[i++]; assert(value && value !== '}', `Missing value: ${key}`); }
      }
      out.push([key, value]);
    }
    if (nested) assert.equal(tokens[i++], '}', 'Unclosed block');
    return out;
  }
  const result = block();
  assert.equal(i, tokens.length, 'Unexpected closing brace');
  return result;
}
const one = (nodes, key) => nodes.find(n => n[0] === key)?.[1];
const namesTree = parse(read('common/dynamic_country_names/00_dynamic_country_names.txt'));
assert.equal(namesTree.filter(n => n[0] === 'DEFAULT').length, 1);
const names = one(namesTree, 'DEFAULT').filter(n => n[0] === 'dynamic_country_name').map(n => n[1]);
const triggers = Object.fromEntries([
  ...parse(read('common/scripted_triggers/aoc_colonial_name_triggers.txt')),
  ...parse(read('common/scripted_triggers/aoc_colonial_nation_triggers.txt')),
]);
const files = dir => fs.readdirSync(dir, {withFileTypes: true}).flatMap(e => e.isDirectory() ? files(path.join(dir, e.name)) : [path.join(dir, e.name)]);
const nameKeys = new Set(names.flatMap(n => [one(n,'name'),one(n,'adjective')]).filter(k => k?.startsWith('colonial_')));
const localization = new Map();
for (const file of files(path.join(root, 'localization/english')).filter(f => f.endsWith('.yml'))) {
  for (const m of fs.readFileSync(file, 'utf8').matchAll(/^\s*([^\s:#]+):\d*\s+"(.*)"/gm)) {
    if (nameKeys.has(m[1])) { assert(!localization.has(m[1]), `Duplicate localization: ${m[1]}`); localization.set(m[1], m[2]); }
  }
}
const definitions = files(path.join(root, 'common/country_definitions')).map(f => fs.readFileSync(f, 'utf8')).join('\n');
const geographic = Object.fromEntries([
  ...parse(read('common/geographic_regions/england_overseas_regions.txt')),
  ...parse(read('common/geographic_regions/aoc_historical_colonial_regions.txt')),
].map(([key,nodes]) => [key, one(nodes,'state_regions').map(n => n[0].replace('STATE_', ''))]));
function evaluate(nodes, env) {
  return nodes.every(([key, value]) => {
    if (key === 'OR') return value.some(n => evaluate([n], env));
    if (key === 'AND' || key === 'scope:actor' || key === 'capital') return evaluate(value, env);
    if (key === 'exists') return value === 'scope:actor' || value === `c:${env.overlord}`;
    if (key === 'has_variable') return value === `${env.region}_subject_var` || (value === 'aoc_was_colonial_nation' && env.wasColonial === true);
    if (key === 'is_direct_subject_of') return value === `c:${env.overlord}`;
    if (key === 'state_region') return value === `s:STATE_${env.state}`;
    if (key === 'is_in_geographic_region') { assert(geographic[value], `Unknown geography: ${value}`); return geographic[value].includes(env.state); }
    if (key === 'is_country_type') return value === env.countryType;
    if (key === 'is_subject_type') return value === env.subjectType;
    if (triggers[key]) return evaluate(triggers[key], env);
    throw Error(`Unhandled naming trigger: ${key}`);
  });
}
// Select by the actual engine priority; same-priority matches must be unambiguous.
const relevant = names.filter(n => one(n, 'name')?.startsWith('colonial_') && !one(n, 'name').startsWith('colonial_admin_'));
function select(env) {
  const matches = relevant.filter(n => evaluate(one(n, 'trigger'), env)).sort((a,b) => Number(one(b,'priority')) - Number(one(a,'priority')));
  if (matches.length > 1) assert.notEqual(one(matches[0], 'priority'), one(matches[1], 'priority'), `Ambiguous name: ${JSON.stringify(env)}`);
  return matches[0] && one(matches[0], 'name');
}
const powers = {castilian:['CAS','SPA'], portuguese:['POR'], french:['FRA'], english:['ENG','GBR'], dutch:['NET','HOL'], danish:['DEN'], swedish:['SWE'], brandenburg:['BBR'], prussian:['PRU'], german:['GER'], belgian:['BEL'], omani:['OMA']};
const regions = ['cape_verde','senegal','zanj','southern_africa','congo','canada','atlantic_coast','pacific_coast','great_plains','central_america','gran_colombia','andes','la_plata','brazil'];
assert(fs.existsSync(path.join(game, 'map_data/state_regions')), 'Game state definitions unavailable');
const stateText = files(path.join(game,'map_data/state_regions')).map(f => fs.readFileSync(f,'utf8')).join('\n');
let cases = 0;
for (const [power, tags] of Object.entries(powers)) for (const overlord of tags) {
  assert(new RegExp(`^${overlord}\\s*\\??=`, 'm').test(definitions), `Unknown country: ${overlord}`);
  for (const region of regions) {
    assert.equal(select({overlord,region,state:'UNSPECIFIED'}), `colonial_${power}_${region}`); cases++;
  }
  for (const [region,state] of [['australia','VICTORIA'],['new_zealand','NORTH_ISLAND']]) {
    for (const identity of [{countryType:'colonial'}, {countryType:'recognized',wasColonial:true}, {subjectType:'subject_type_colony'}]) {
      assert.equal(select({overlord,region,state,...identity}), `colonial_${power}_${region}`); cases++;
    }
    assert.equal(select({overlord,region,state,countryType:'unrecognized',subjectType:'subject_type_protectorate'}), undefined); cases++;
  }
}
for (const n of relevant) {
  for (const field of ['name','adjective']) assert(localization.has(one(n,field)), `Missing ${one(n,field)}`);
  const key = one(n,'name');
  if (!key.includes('_seat_')) continue;
  const actor = one(one(n,'trigger'), 'scope:actor');
  const variable = one(actor,'has_variable');
  const region = variable ? variable.replace(/_subject_var$/, '') : 'australia';
  const power = key.split('_')[1];
  const cap = one(actor,'capital');
  const area = one(cap,'is_in_geographic_region');
  const states = area ? geographic[area] : (one(cap,'OR') || cap).map(n => n[1].replace('s:STATE_', ''));
  for (const state of states) {
    assert(new RegExp(`\\bSTATE_${state}\\s*=`).test(stateText), `Unknown state: ${state}`);
    for (const overlord of powers[power]) { assert.equal(select({overlord,region,state,countryType:'colonial'}), key); cases++; }
    assert.equal(select({overlord:'UNRELATED',region,state,countryType:'colonial'}), undefined); cases++;
  }
}
for (const region of regions) { assert.equal(select({overlord:null,region,state:'UNSPECIFIED'}), undefined); cases++; }
const locBytes = fs.readFileSync(path.join(root,'localization/english/aoc_african_colonial_names_l_english.yml'));
assert.equal(locBytes.subarray(0,3).toString('hex'), 'efbbbf');
assert.equal(fs.readFileSync(path.join(root,'localization/english/aoc_american_australasian_colonial_names_l_english.yml')).subarray(0,3).toString('hex'), 'efbbbf');
for (const [region,area] of [['australia','geographic_region_aoc_england_australia'],['new_zealand','geographic_region_aoc_england_new_zealand']]) {
  const fallback = names.find(n => one(n,'name') === `colonial_admin_${region}`);
  assert.equal(one(fallback,'priority'),'100');
  for (const field of ['name','adjective']) assert(localization.has(one(fallback,field)));
  for (const state of geographic[area]) {
    assert(new RegExp(`\\bSTATE_${state}\\s*=`).test(stateText), `Unknown state: ${state}`);
    for (const overlord of [null,'UNRELATED']) {
      assert.equal(select({overlord,region,state,countryType:'colonial'}),undefined); cases++;
      assert(evaluate(one(fallback,'trigger'),{overlord,region,state,countryType:'colonial'})); cases++;
    }
    assert(!evaluate(one(fallback,'trigger'),{region,state,countryType:'unrecognized'})); cases++;
  }
}
console.log(`PASS: ${cases} naming cases across Africa, the Americas, Australia and New Zealand; localization, tags, states, priorities, independence, and local-country guards valid.`);

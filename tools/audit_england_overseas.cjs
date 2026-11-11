// Static reference and progression audit. Usage: node tools/audit_england_overseas.cjs
// Pass a different vanilla game directory as the first argument if necessary.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const game = process.argv[2] || 'C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game';
const read = p => fs.readFileSync(path.join(root, p), 'utf8').replace(/^\uFEFF/, '');
const files = [
 'common/company_types/england_overseas_companies.txt',
 'common/geographic_regions/england_overseas_regions.txt',
 'common/journal_entries/england_overseas.txt',
 'common/scripted_buttons/england_overseas_buttons.txt',
 'common/scripted_effects/aoc_country_identity_effects.txt',
 'common/scripted_effects/england_overseas_effects.txt',
 'common/scripted_triggers/england_overseas_triggers.txt',
 'common/static_modifiers/england_overseas_modifiers.txt',
 'events/england_overseas_events.txt'
];
function parse(text, file) {
 const tokens = [...text.matchAll(/#[^\r\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>!?"#]+/g)]
  .map(m => m[0]).filter(t => !t.startsWith('#'));
 let i = 0;
 function scalar() {
  const t = tokens[i++];
  assert(t !== undefined && t !== '}', `${file}: missing value`);
  return t.startsWith('"') ? JSON.parse(t) : t;
 }
 function block(nested = false) {
  const nodes = [];
  while (i < tokens.length && tokens[i] !== '}') {
   const key = scalar();
   assert(key !== '{', `${file}: anonymous block`);
   if (['=','?=','>=','<=','!=','>','<'].includes(tokens[i])) {
    const op = tokens[i++];
    let value;
    if (tokens[i] === '{') { i++; value = block(true); }
    else value = scalar();
    nodes.push({key, op, value});
   } else nodes.push({key});
  }
  if (nested) assert.equal(tokens[i++], '}', `${file}: unclosed block`);
  return nodes;
 }
 const result = block();
 assert.equal(i, tokens.length, `${file}: unexpected closing brace`);
 return result;
}
function walk(nodes, fn, parents = []) {
 for (const n of nodes) {
  fn(n, parents);
  if (Array.isArray(n.value)) walk(n.value, fn, [...parents, n.key]);
 }
}
const one = (nodes, key) => {
 const node = nodes.find(n => n.key === key);
 assert(node, `Missing ${key}`);
 return node;
};
const trees = new Map(files.map(f => [f, parse(read(f), f)]));
const definitions = new Map();
for (const [f, nodes] of trees) for (const n of nodes) {
 if (Array.isArray(n.value)) {
  assert(!definitions.has(n.key), `Duplicate definition: ${n.key}`);
  definitions.set(n.key, {file:f, node:n});
 }
}
const directoryCache = new Map();
function collect(dir) {
 if (!fs.existsSync(dir)) return '';
 return fs.readdirSync(dir, {withFileTypes:true}).map(e => {
  const p = path.join(dir, e.name);
  return e.isDirectory() ? collect(p) : e.name.endsWith('.txt') ? fs.readFileSync(p, 'utf8') : '';
 }).join('\n');
}
function existsSymbol(dir, key) {
 const cacheKey = dir + ':ids';
 if (!directoryCache.has(cacheKey)) {
  const source = collect(path.join(game, dir)) + '\n' + collect(path.join(root, dir));
  directoryCache.set(cacheKey, new Set([...source.matchAll(/^(?:\uFEFF)?([\w.]+)\s*=/gm)].map(m=>m[1])));
 }
 assert(directoryCache.get(cacheKey).has(key), `Undefined ${dir}: ${key}`);
}
const localizationPath = 'localization/english/england_overseas_l_english.yml';
const rawLoc = fs.readFileSync(path.join(root,localizationPath));
assert.deepEqual([...rawLoc.subarray(0,3)], [239,187,191], 'Localization needs a UTF-8 BOM');
const localization = new Map();
for (const line of read(localizationPath).split(/\r?\n/).slice(1).filter(Boolean)) {
 const m = line.match(/^ ([\w.]+): ("(?:\\.|[^"\\])*")$/);
 assert(m, `Malformed localization: ${line}`);
 assert(!localization.has(m[1]), `Duplicate localization: ${m[1]}`);
 localization.set(m[1], JSON.parse(m[2]));
}
const requireLoc = key => assert(localization.has(key), `Missing English localization: ${key}`);
const referenceTypes = {
 has_building:'common/buildings', is_building_type:'common/buildings', building:'common/buildings',
 base_good:'common/goods', has_technology_researched:'common/technology/technologies',
 is_in_geographic_region:'common/geographic_regions',
 is_subject_type:'common/subject_types',
 add_declared_interest:'common/strategic_regions',
 tag:'common/country_definitions'
};
let assetCount = 0, referenceCount = 0;
for (const [f, nodes] of trees) walk(nodes, (n, parents) => {
 if (typeof n.value === 'string') {
  if (referenceTypes[n.key]) { existsSymbol(referenceTypes[n.key],n.value); referenceCount++; }
  if (['text','title','desc','flavor'].includes(n.key) && /^(aoc_england_|england_overseas\.)/.test(n.value)) requireLoc(n.value);
  if (n.key === 'name' && parents.at(-1)?.startsWith('aoc_england_charter_')) requireLoc(n.value);
  if (n.key === 'scripted_button') assert(definitions.has(n.value), `Missing button ${n.value}`);
  if (n.key === 'id' && parents.at(-1) === 'trigger_event') assert(definitions.has(n.value), `Missing event ${n.value}`);
  if (n.key === 'name' && parents.at(-1) === 'add_modifier') existsSymbol('common/static_modifiers',n.value);
  if (/^aoc_england_/.test(n.key) && ['yes','no'].includes(n.value)) assert(definitions.has(n.key), `Missing custom trigger/effect ${n.key}`);
  for (const [,prefix,key] of n.value.matchAll(/\b(company_type|law_type|g|s|c):([\w]+)/g)) {
   existsSymbol({company_type:'common/company_types',law_type:'common/laws',g:'common/goods',s:'map_data/state_regions',c:'common/country_definitions'}[prefix],key);
  }
  if (['icon','texture','background'].includes(n.key)) {
   assert(fs.existsSync(path.join(root,n.value)) || fs.existsSync(path.join(game,n.value)), `Missing asset ${n.value}`);
   assetCount++;
  }
 } else if (!n.op && parents.some(p => ['building_types','extension_building_types','possible_prestige_goods','state_regions'].includes(p))) {
  const dir = parents.includes('possible_prestige_goods') ? 'common/prestige_goods' : parents.includes('state_regions') ? 'map_data/state_regions' : 'common/buildings';
  existsSymbol(dir,n.key);
 }
});
const journals = trees.get('common/journal_entries/england_overseas.txt');
assert.equal(journals.length,6);
const journalIcons = new Set();
for (const j of journals) {
 const icon = one(j.value,'icon').value;
 assert(icon.startsWith('gfx/interface/icons/event_icons/england_overseas/'), `${j.key}: custom heraldic icon missing`);
 journalIcons.add(icon);
 const dds = fs.readFileSync(path.join(root,icon));
 assert.equal(dds.toString('ascii',0,4),'DDS ');
 assert.equal(dds.readUInt32LE(12),256, `${icon}: height`);
 assert.equal(dds.readUInt32LE(16),256, `${icon}: width`);
 assert.equal(dds.readUInt32LE(28),9, `${icon}: full mip chain`);
 const format = dds.toString('ascii',84,88);
 assert(['DXT5','DX10'].includes(format), `${icon}: unsupported DDS texture`);
 if (format === 'DX10') {
  assert([77,78,98,99].includes(dds.readUInt32LE(128)), `${icon}: expected BC3 or BC7 format`);
  assert.equal(dds.readUInt32LE(132),3, `${icon}: expected 2D texture`);
  assert.equal(dds.readUInt32LE(140),1, `${icon}: expected one array layer`);
 }
 assert.equal(dds.length,87536+(format==='DX10'?20:0), `${icon}: mip payload length`);
 const lobby=one(j.value,'is_shown_in_lobby');
 assert(JSON.stringify(lobby).includes('c:ENG') && JSON.stringify(lobby).includes('c:GBR'), `${j.key}: England and Britain lobby visibility`);
 assert(!one(j.value,'possible').value.some(n=>n.key==='aoc_england_overseas_country'), `${j.key}: redundant visible country eligibility`);
 for (const suffix of ['', '_reason', '_status']) requireLoc(j.key+suffix);
 const done = j.key.replace('je_aoc_england_','aoc_england_')+'_completed';
 assert(JSON.stringify(one(j.value,'possible')).includes(done), `${j.key}: no completion lock`);
 walk(j.value, n => {
  if (n.key==='add_modifier') assert.equal(one(n.value,'years').value,'25', `${j.key}: reward must last 25 years`);
 });
}
assert.equal(journalIcons.size,6,'Every journal needs a distinct icon');
assert(!read(localizationPath).includes('ROOT.GetCountry'), 'Journal localization needs the journal country scope, not ROOT');
const effects = trees.get('common/scripted_effects/england_overseas_effects.txt');
const buttons = trees.get('common/scripted_buttons/england_overseas_buttons.txt');
assert.equal(buttons.length,5);
for (const button of buttons) {
 const possible = JSON.stringify(one(button.value,'possible'));
 assert(possible.includes('is_at_war') && possible.includes('is_diplomatic_play_committed_participant'));
 const createNodes = [];
 walk(button.value,n => { if(n.key==='create_country') createNodes.push(n); });
 assert.equal(createNodes.length,1);
 const tag = one(createNodes[0].value,'tag').value;
 assert(['SAF','BIC','AST','NZL','HBC'].includes(tag));
 assert(!JSON.stringify(button).includes('"HAB"'), 'HAB is Austria');
 const id = button.key.replace('aoc_england_charter_','');
 assert(JSON.stringify(button).includes(`aoc_england_${id}_endowed`), 'Missing endowment lock');
}
// All modifier tokens must exist in the engine log, or be a valid dynamic building modifier.
const modifierDocs=read('docs/modifiers.log');
for (const [f, nodes] of trees) if (f.includes('static_modifiers') || f.includes('company_types')) {
 walk(nodes,(n,parents) => {
  if (typeof n.value !== 'string' || !/^-?\d+(\.\d+)?$/.test(n.value)) return;
  if (!f.includes('static_modifiers') && !parents.includes('prosperity_modifier')) return;
  const building=n.key.match(/^(building_.+)_throughput_add$/);
  if (new RegExp('^'+n.key+':','m').test(modifierDocs)) return;
  if (building) existsSymbol('common/buildings',building[1]);
  else assert.fail(`Unknown modifier: ${n.key}`);
 });
}
// Parse the modified integration files as well.
for(const f of ['common/journal_entries/england.txt','common/scripted_buttons/england_canada_colonization_buttons.txt','common/scripted_buttons/00_colonial_administration_buttons.txt','common/dynamic_country_names/00_dynamic_country_names.txt']) {
 parse(read(f),f);
 assert(!read(f).includes('scripted_button = je_england_canada_hudsons_bay'));
}
const triggerNodes=trees.get('common/scripted_triggers/england_overseas_triggers.txt');
for(const [name,tag] of [['cape_station_ready','SAF'],['cape_developed','SAF'],['indian_presidencies','BIC']]) {
 const body=one(triggerNodes,'aoc_england_'+name).value;
 assert(body.some(n=>n.key==='exists'&&n.value==='c:'+tag), `${name}: absent tag must not pass`);
}
// Exercise the timer operations from the actual parsed monthly pulse.
const navy=one(journals,'je_aoc_england_royal_navy');
const pulse=one(one(navy.value,'on_monthly_pulse').value,'effect').value;
const gain=Number(one(one(one(pulse,'if').value,'change_variable').value,'add').value);
const reset=Number(one(one(one(pulse,'else').value,'set_variable').value,'value').value);
const navyOutcome=navy.value.find(n=>n.key==='outcome'&&!n.value.some(c=>c.key==='flags'));
const target=Number(one(one(one(navyOutcome.value,'trigger').value,'custom_tooltip').value,'var:aoc_england_navy_months').value);
let months=0;
for(let i=0;i<119;i++) months+=gain;
assert(months<target);
months=reset;
assert.equal(months,0);
for(let i=0;i<120;i++) months+=gain;
assert.equal(months,target);
// Territorial targets use half of the complete region, never a split-state count.
for(const id of ['australia','new_zealand']) {
 const census=one(effects,`aoc_england_${id}_census_effect`);
 const mul=census.value.filter(n=>n.key==='change_variable').find(n=>one(n.value,'name').value===`aoc_england_${id}_target`);
 const share=Number(one(mul.value,'multiply').value);
 assert.equal(share,0.5);
 assert(49 < 100*share && 50 >= 100*share);
 assert(50 < 101*share && 51 >= 101*share);
}
for(const id of ['cape_colony_name','cape_colony_adjective','east_india_name','east_india_adjective']) requireLoc('aoc_england_'+id);
console.log(`PASS: ${journals.length} journals, ${buttons.length} charters, ${definitions.size} definitions, ${localization.size} English strings, ${referenceCount} references, ${assetCount} assets.`);
console.log('PASS: syntax, reward durations, completion/endowment guards, absent tags, naval reset/120-month boundary, and 50% territorial boundaries.');
console.log('Static audit only. Company creation, scope evaluation, UI and gameplay still require Victoria 3 verification.');

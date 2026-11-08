/** Build or audit the 1444 population history. Run from a checkout of the
 * pre-pass population files with --write. Without --write, audit the result.
 * Use --write --source-ref <git-ref> to rebuild from a pre-pass revision.
 * Use --report to print state and owner demographics as JSON.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { parse, children, scalar, words, read, files, root, base } = require('./audit_map_ownership.cjs');
const { groups, states, shares } = require('./population_1444_profiles.cjs');

const popDir = path.join(root, 'common/history/pops');
const marker = '# Population history revised for 1444';
const owners = new Map();
const regions = new Map();
const cultureDefinitions = new Map();
const religionDefinitions = new Map();

function loadDefinitions(folder, definitions, includeBase) {
  const paths = files(path.join(root, 'common', folder));
  if (includeBase) paths.unshift(...files(path.join(base, 'common', folder)));
  for (const p of paths) {
    for (const n of parse(read(p))) {
      if (Array.isArray(n.value)) definitions.set(n.key.replace(/^(REPLACE|INJECT):/, ''), n);
    }
  }
}
loadDefinitions('cultures', cultureDefinitions, true);
loadDefinitions('religions', religionDefinitions, false);

function loadOwnership() {
  for (const f of files(path.join(root, 'common/history/states'))) {
    for (const top of parse(read(f)).filter(n => n.key === 'STATES')) {
      for (const state of top.value) {
        const name = state.key.slice('s:STATE_'.length);
        const splits = owners.get(name) || new Map();
        for (const split of children(state, 'create_state')) {
          const tag = scalar(split, 'country').slice(2);
          splits.set(tag, [...(splits.get(tag) || []), ...words(split, 'owned_provinces')]);
        }
        owners.set(name, splits);
      }
    }
  }
  for (const f of files(path.join(base, 'common/strategic_regions'))) {
    for (const region of parse(read(f))) {
      regions.set(region.key.slice('region_'.length), words(region, 'states').map(s => s.slice(6)));
    }
  }
}
loadOwnership();

function loadPops(sourceRef) {
  const entries = new Map();
  const sources = new Map();
  for (const f of files(popDir)) {
    const original = sourceRef
      ? execFileSync('git', ['show', `${sourceRef}:${path.relative(root, f).replaceAll('\\', '/')}`], { cwd: root, encoding: 'utf8' })
      : fs.readFileSync(f, 'utf8');
    const content = original.replace(/^\uFEFF/, '');
    const top = parse(content);
    assert.equal(top.length, 1, f);
    assert.equal(top[0].key, 'POPS', f);
    sources.set(f, { content, nodes: top[0].value, bom: original.startsWith('\uFEFF') });
    for (const state of top[0].value) {
      const name = state.key.slice('s:STATE_'.length);
      const pops = entries.get(name) || [];
      for (const split of state.value) {
        assert(split.key.startsWith('region_state:'), split.key);
        const owner = split.key.slice('region_state:'.length);
        for (const pop of split.value) {
          assert.equal(pop.key, 'create_pop');
          assert(pop.value.every(n => ['size', 'culture', 'religion', 'pop_type'].includes(n.key)));
          pops.push({
            owner, culture: scalar(pop, 'culture'), religion: scalar(pop, 'religion'),
            type: scalar(pop, 'pop_type') || '', size: Number(scalar(pop, 'size')),
          });
        }
      }
      entries.set(name, pops);
    }
  }
  return { entries, sources };
}

function total(pops) {
  return pops.reduce((sum, p) => sum + p.size, 0);
}

// Largest remainder apportionment keeps each state and region total exact.
function apportion(totalSize, weights) {
  if (!totalSize) return weights.map(() => 0);
  const sum = weights.reduce((a, b) => a + b, 0);
  assert(sum > 0, 'Cannot apportion population without weights');
  const quotas = weights.map(w => totalSize * w / sum);
  const rounded = quotas.map(Math.floor);
  const order = quotas.map((q, i) => ({ i, remainder: q - rounded[i] }))
    .sort((a, b) => b.remainder - a.remainder || a.i - b.i);
  const left = totalSize - rounded.reduce((a, b) => a + b, 0);
  for (const { i } of order.slice(0, left)) rounded[i]++;
  return rounded;
}

function populationGroups() {
  const explicit = new Set(groups.flatMap(([, , list]) => list.split(' ').filter(x => !x.startsWith('@'))));
  const assigned = new Set();
  const result = groups.map(([label, target, list]) => {
    const names = list.split(' ').flatMap(x => x.startsWith('@')
      ? regions.get(x.slice(1)).filter(s => !explicit.has(s))
      : [x]);
    for (const name of names) {
      assert(owners.has(name), `Unknown state: ${name}`);
      assert(!assigned.has(name), `Duplicate group assignment: ${name}`);
      assigned.add(name);
    }
    return { label, target: target * 1000, names };
  });
  assert.equal(assigned.size, owners.size, [...owners.keys()].filter(s => !assigned.has(s)).join(', '));
  return result;
}

const englishAndFrench = new Set(('WALES MIDLANDS EAST_ANGLIA WEST_COUNTRY HOME_COUNTIES YORKSHIRE LANCASHIRE HIGHLANDS LOWLANDS ULSTER LEINSTER CONNAUGHT MUNSTER CHAMPAGNE ILE_DE_FRANCE ORLEANS FRENCH_LOW_COUNTRIES BRITTANY NORMANDY PICARDY MAINE_ANJOU BURGUNDY POITOU GUYENNE LANGUEDOC AQUITAINE RHONE AUVERGNE_LIMOUSIN').split(' '));
const iran = new Set('IRAKAJEMI LARISTAN SISTAN KHUZESTAN TABRIZ URMIA PERSIAN_KURDISTAN LURISTAN KERMAN SEMNAN'.split(' '));
const byzantine = new Set('PELOPONNESE IONIAN_ISLANDS ATTICA THESSALIA MACEDONIA WESTERN_THRACE CRETE WEST_AEGEAN_ISLANDS EASTERN_THRACE HUDAVENDIGAR AYDIN EAST_AEGEAN_ISLANDS TRABZON CYPRUS'.split(' '));
const easternJews = new Set('DONGOLA ALEPPO PALESTINE SYRIA LEBANON BAGHDAD BASRA MOSUL HEDJAZ YEMEN ISFAHAN FARS TABRIZ URMIA KHORASAN IRAKAJEMI ERZURUM DIYARBAKIR'.split(' '));
const americas = new Set(['canada', 'pacific_coast', 'great_plains', 'atlantic_coast', 'central_america', 'brazil', 'andes', 'la_plata', 'gran_colombia'].flatMap(r => regions.get(r)));
const northEurope = new Set([...regions.get('central_europe'), ...regions.get('eastern_europe'), 'ALSACE_LORRAINE', 'RHINELAND', 'NORTH_RHINE']);
const iberia = new Set(groups[7][2].split(' ').concat(groups[6][2].split(' ')));
const postReformation = new Set(['protestant', 'reformed', 'anglican', 'calvinist']);
const mexican = new Set(['nahua', 'tarascan', 'mixtec', 'zapotec', 'otomi', 'totonac']);
const andean = new Set(['quechua', 'aimara']);
const andes = new Set(regions.get('andes'));
const lateJewishShares = new Set([...regions.get('eastern_europe'), 'BESSARABIA', 'MOLDAVIA']);
const southernAfrica = new Set(regions.get('southern_africa'));

function periodPops(name, source) {
  const result = [];
  const isAmerica = americas.has(name);
  const dominant = source.filter(p => p.religion !== 'jewish').sort((a, b) => b.size - a.size)[0];
  for (const original of source) {
    const pop = { ...original };
    if (!pop.religion) pop.religion = scalar(cultureDefinitions.get(pop.culture), 'religion');
    if (isAmerica || ['TAHITI', 'CELEBES', 'NORTH_SUMATRA', 'ZULULAND', 'MINDANAO'].includes(name)) {
      if (pop.religion === 'catholic' || postReformation.has(pop.religion)) pop.religion = 'animist';
    } else if (postReformation.has(pop.religion)) {
      pop.religion = 'catholic';
    }

    if (pop.religion === 'jewish' && pop.culture === 'sephardic') {
      if (byzantine.has(name)) pop.culture = 'aoc_romaniote';
      else if (easternJews.has(name)) pop.culture = 'aoc_eastern_jewish';
      else if (northEurope.has(name)) pop.culture = 'ashkenazi';
      else if ((englishAndFrench.has(name) || !iberia.has(name)) && dominant) {
        // Most of these tiny entries are uniform converter minorities. Keep
        // documented Iberian, Mediterranean and Maghrebi communities.
        const plausible = ['PROVENCE', 'SAVOY', 'VENETIA', 'SICILY', 'LAZIO', 'CAMPANIA', 'TUNISIA', 'FEZ', 'ALGIERS', 'ORAN', 'CONSTANTINE', 'MARRAKECH', 'TRIPOLI', 'LIBYA'].includes(name);
        if (!plausible) {
          pop.culture = dominant.culture;
          pop.religion = dominant.religion;
        }
      }
    }
    if (pop.religion === 'sikh') pop.religion = 'hindu';
    if (pop.religion === 'jewish' && dominant && englishAndFrench.has(name) && ['sephardic', 'ashkenazi'].includes(pop.culture)) {
      pop.culture = dominant.culture;
      pop.religion = dominant.religion;
    }
    if (pop.religion === 'jewish' && dominant && lateJewishShares.has(name) && pop.size > 4) {
      // Late medieval Jewish communities predate the much larger shares
      // carried over from the nineteenth-century Polish-Lithuanian lands.
      const [local, jewish] = apportion(pop.size, [90, 10]);
      result.push({ ...pop, culture: dominant.culture, religion: dominant.religion, size: local });
      pop.size = jewish;
    }
    if (southernAfrica.has(name) && pop.culture === 'boer') {
      pop.culture = dominant.culture;
      pop.religion = 'animist';
    }
    if (name === 'CELEBES' && pop.culture === 'dutch') pop.culture = 'moluccan';
    if (iran.has(name) && pop.religion === 'shiite') {
      // Keep minority centers, but unwind the later Safavid-era majority.
      const [sunni, shiite] = apportion(pop.size, [85, 15]);
      result.push({ ...pop, religion: 'sunni', size: sunni });
      pop.size = shiite;
    }
    if (pop.culture === 'manchu') {
      pop.culture = 'aoc_jurchen';
      if (pop.religion === 'confucian' || pop.religion === 'tengri_pagan_reformed') pop.religion = 'animist';
    }
    if (pop.culture === 'mongol' && pop.religion === 'gelugpa') {
      const [tengri, buddhist] = apportion(pop.size, [90, 10]);
      result.push({ ...pop, religion: 'tengri_pagan_reformed', size: tengri });
      pop.size = buddhist;
    }
    if (pop.religion === 'animist') {
      if (isAmerica && mexican.has(pop.culture)) pop.religion = 'aoc_mesoamerican';
      if (isAmerica && pop.culture === 'mayan') pop.religion = 'aoc_maya';
      if (andes.has(name) && andean.has(pop.culture)) pop.religion = 'aoc_andean';
    }
    result.push(pop);
  }
  return result.filter(p => p.size > 0);
}

function profile(name, owner, source) {
  const specific = shares[`${name}:${owner}`];
  const whole = shares[name];
  if (!specific && !whole) return periodPops(name, source);
  const rows = parseShares(specific || whole).map(pop => ({ ...pop, owner, type: '' }));
  // Preserve the starting share of explicitly enslaved people where one
  // exists. Apply the new identities to free and enslaved pops alike.
  const slaveShare = total(source.filter(p => p.type === 'slaves')) / (total(source) || 1);
  return rows.flatMap(pop => slaveShare
    ? [{ ...pop, size: pop.size * (1 - slaveShare) }, { ...pop, type: 'slaves', size: pop.size * slaveShare }]
    : [pop]);
}

function parseShares(profile) {
  return profile.split(' ').map(entry => {
    const [culture, religion, weight] = entry.split('/');
    return { culture, religion, size: Number(weight) };
  });
}

function revisedPops(name, size, original) {
  if (!size) return [];
  const splits = [...owners.get(name)];
  const valid = original.filter(p => owners.get(name).has(p.owner));
  const inferredWeight = total(valid) / splits.reduce((sum, [, provinces]) => sum + provinces.length, 0);
  // Existing split weights retain local settlement patterns. Newly populated
  // splits get a conservative area proxy based on the number of map provinces.
  const splitWeights = splits.map(([tag, provinces]) =>
    total(valid.filter(p => p.owner === tag)) || Math.max(1, inferredWeight * provinces.length * 0.35));
  const ownerSizes = apportion(size - splits.length, splitWeights).map(n => n + 1);
  return splits.flatMap(([owner], i) => {
    const source = valid.filter(p => p.owner === owner);
    if (!source.length && !shares[`${name}:${owner}`] && !shares[name]) {
      throw new Error(`No demographic profile for new split ${name}:${owner}`);
    }
    const merged = new Map();
    for (const p of profile(name, owner, source)) {
      const key = [p.culture, p.religion, p.type].join('/');
      const old = merged.get(key);
      merged.set(key, old ? { ...old, size: old.size + p.size } : p);
    }
    const pops = [...merged.values()];
    const sizes = apportion(ownerSizes[i], pops.map(p => p.size));
    return pops.map((p, j) => ({ ...p, size: sizes[j] })).filter(p => p.size > 0);
  });
}

function renderState(name, pops) {
  const lines = [`s:STATE_${name} = {`];
  for (const owner of owners.get(name).keys()) {
    const local = pops.filter(p => p.owner === owner);
    if (!local.length) continue;
    lines.push(`\t\tregion_state:${owner} = {`);
    for (const { culture, religion, type, size } of local) {
      lines.push('\t\t\tcreate_pop = {', `\t\t\t\tculture = ${culture}`, `\t\t\t\treligion = ${religion}`);
      if (type) lines.push(`\t\t\t\tpop_type = ${type}`);
      lines.push(`\t\t\t\tsize = ${size}`, '\t\t\t}');
    }
    lines.push('\t\t}');
  }
  if (!pops.length) lines.push('\t\t# No permanent population in 1444.');
  lines.push('\t}');
  return lines.join('\n');
}

function validate(entries, populations) {
  assert.equal(entries.size, owners.size);
  for (const [key, profile] of Object.entries(shares)) {
    const [name, owner] = key.split(':');
    assert(owners.has(name) && (!owner || owners.get(name).has(owner)), `Unused profile: ${key}`);
    const rows = parseShares(profile);
    assert(rows.every(row => row.size > 0) && Math.abs(total(rows) - 100) < 1e-8, `Invalid percentages: ${key}`);
  }
  for (const { label, target, names } of populations) {
    assert.equal(names.reduce((sum, name) => sum + total(entries.get(name)), 0), target, label);
    for (const name of names) {
      const pops = entries.get(name);
      assert(pops.length || states[name] === 0, `Missing population: ${name}`);
      if (Object.hasOwn(states, name)) assert.equal(total(pops), states[name] * 1000, name);
      const seen = new Set();
      for (const p of pops) {
        assert(owners.get(name).has(p.owner), `Unowned population scope: ${name}:${p.owner}`);
        assert(cultureDefinitions.has(p.culture), `Undefined culture ${p.culture} in ${name}`);
        assert(religionDefinitions.has(p.religion), `Undefined religion ${p.religion} in ${name}`);
        assert(Number.isSafeInteger(p.size) && p.size > 0, `Invalid population in ${name}`);
        const key = [p.owner, p.culture, p.religion, p.type].join('/');
        assert(!seen.has(key), `Duplicate population ${name}:${key}`);
        seen.add(key);
      }
      if (pops.length) assert.equal(new Set(pops.map(p => p.owner)).size, owners.get(name).size, `Empty split: ${name}`);
      for (const owner of owners.get(name).keys()) {
        const planned = shares[`${name}:${owner}`] || shares[name];
        if (!planned) continue;
        const split = pops.filter(p => p.owner === owner);
        for (const { culture, religion, size: percent } of parseShares(planned)) {
          const actual = total(split.filter(p => p.culture === culture && p.religion === religion));
          assert(Math.abs(actual - total(split) * percent / 100) < 2, `Profile drift: ${name}:${owner} ${culture}/${religion}`);
        }
      }
    }
  }
}

function report(entries, populations) {
  function summarize(pops) {
    const size = total(pops);
    function distribution(key) {
      const grouped = new Map();
      for (const p of pops) grouped.set(p[key], (grouped.get(p[key]) || 0) + p.size);
      return Object.fromEntries([...grouped].sort((a, b) => b[1] - a[1]).map(([id, count]) =>
        [id, { population: count, percent: Number((100 * count / size).toFixed(4)) }]));
    }
    return { population: size, cultures: distribution('culture'), religions: distribution('religion') };
  }
  const data = populations.map(({ label, target, names }) => ({
    region: label, population: target,
    states: Object.fromEntries(names.map(name => [`STATE_${name}`, {
      ...summarize(entries.get(name)),
      owners: Object.fromEntries([...owners.get(name)].map(([tag, provinces]) =>
        [tag, { provinces, ...summarize(entries.get(name).filter(p => p.owner === tag)) }])),
    }])),
  }));
  console.log(JSON.stringify(data, null, 2));
}

const sourceIndex = process.argv.indexOf('--source-ref');
const sourceRef = sourceIndex === -1 ? undefined : process.argv[sourceIndex + 1];
if (sourceIndex !== -1) assert(sourceRef && /^[\w./~-]+$/.test(sourceRef) && !sourceRef.startsWith('-') &&
  process.argv.includes('--write'), '--source-ref requires a Git revision and --write');
const { entries, sources } = loadPops(sourceRef);
const populations = populationGroups();
if (process.argv.includes('--write')) {
  assert([...sources.values()].every(({ content }) => !content.includes(marker)), 'Population pass already applied');
  const revised = new Map();
  for (const { label, target, names } of populations) {
    const fixed = names.filter(n => Object.hasOwn(states, n));
    const flexible = names.filter(n => !Object.hasOwn(states, n));
    const remaining = target - fixed.reduce((sum, n) => sum + 1000 * states[n], 0);
    assert(remaining >= 0 && (flexible.length || remaining === 0), label);
    const sizes = apportion(remaining, flexible.map(n => total(entries.get(n))));
    for (const n of fixed) revised.set(n, revisedPops(n, states[n] * 1000, entries.get(n)));
    flexible.forEach((n, i) => revised.set(n, revisedPops(n, sizes[i], entries.get(n))));
  }
  validate(revised, populations);
  const written = new Set();
  for (const [f, { content, nodes, bom }] of sources) {
    const replacements = nodes.map(n => {
      const name = n.key.slice('s:STATE_'.length);
      const replacement = written.has(name) ? '' : renderState(name, revised.get(name));
      written.add(name);
      return [n.start, n.end, replacement];
    });
    let output = content;
    const newline = content.includes('\r\n') ? '\r\n' : '\n';
    for (const [start, end, replacement] of replacements.reverse()) {
      output = output.slice(0, start) + replacement.replaceAll('\n', newline) + output.slice(end);
    }
    output = marker + newline + output;
    output = output.replace(/(?:\r?\n[\t ]*){3,}/g, newline + newline);
    fs.writeFileSync(f, (bom ? '\uFEFF' : '') + output);
  }
  console.log(`Updated ${written.size} states.`);
} else {
  validate(entries, populations);
  if (process.argv.includes('--report')) report(entries, populations);
  else console.log(`Verified ${entries.size} states, ${populations.length} regional targets and ${total([...entries.values()].flat()).toLocaleString('en-US')} people.`);
}

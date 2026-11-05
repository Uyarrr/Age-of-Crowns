/** Compare starting ownership with the installed game's land regions.
 * Usage: node tools/audit_map_ownership.cjs [--json]
 * Set VICTORIA3_GAME_DIR to audit another installation's game directory.
 */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const base = process.env.VICTORIA3_GAME_DIR || 'C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game';

function parse(text) {
  const tokens = [...text.matchAll(/#[^\n]*|"[^"\\]*(?:\\.[^"\\]*)*"|\?=|[{}=]|[^\s{}=#?]+/g)]
    .filter(m => !m[0].startsWith('#'));
  let i = 0;
  function block(nested = false) {
    const nodes = [];
    while (i < tokens.length && tokens[i][0] !== '}') {
      const token = tokens[i++];
      const node = { key: token[0], value: null, start: token.index, end: token.index + token[0].length };
      if (['=', '?='].includes(tokens[i]?.[0])) {
        i++;
        if (!tokens[i]) throw new Error('Missing value');
        if (['rgb', 'hsv', 'hsv360'].includes(tokens[i][0]) && tokens[i + 1]?.[0] === '{') i++;
        node.value = tokens[i][0] === '{' ? (i++, block(true)) : tokens[i++][0];
        node.end = tokens[i - 1].index + tokens[i - 1][0].length;
      }
      nodes.push(node);
    }
    if (nested) {
      if (tokens[i]?.[0] !== '}') throw new Error('Unclosed block');
      i++;
    }
    return nodes;
  }
  const nodes = block();
  if (i !== tokens.length) throw new Error('Unexpected closing brace');
  return nodes;
}
const children = (node, key) => Array.isArray(node.value) ? node.value.filter(n => n.key === key) : [];
const scalar = (node, key) => children(node, key)[0]?.value;
const words = (node, key) => (children(node, key)[0]?.value || []).map(n => n.key.replaceAll('"', ''));
const canonical = p => p.replaceAll('"', '').toUpperCase();
const read = p => fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '');
const files = dir => fs.readdirSync(dir).filter(n => n.endsWith('.txt')).sort().map(n => path.join(dir, n));

function audit() {
  const regions = new Map();
  const mapDir = path.join(base, 'map_data/state_regions');
  const localMapDir = path.join(root, 'map_data/state_regions');
  const effectiveFiles = new Map(files(mapDir).map(p => [path.basename(p), p]));
  if (fs.existsSync(localMapDir)) for (const p of files(localMapDir)) effectiveFiles.set(path.basename(p), p);
  for (const p of effectiveFiles.values()) {
    for (const n of parse(read(p))) {
      // Sea regions have no subsistence building and must remain unowned.
      if (n.key.startsWith('STATE_') && scalar(n, 'subsistence_building')) regions.set(n.key, n);
    }
  }
  const ownership = new Map();
  for (const p of files(path.join(root, 'common/history/states'))) {
    for (const top of parse(read(p))) {
      if (top.key !== 'STATES') continue;
      for (const s of top.value) {
        for (const c of children(s, 'create_state')) {
          const state = s.key.replace(/^s:/, '');
          if (!ownership.has(state)) ownership.set(state, []);
          for (const province of words(c, 'owned_provinces')) ownership.get(state).push({ province: canonical(province), owner: scalar(c, 'country'), file: path.relative(root, p) });
        }
      }
    }
  }
  const issues = [];
  for (const [state, n] of regions) {
    const expected = new Set(words(n, 'provinces').map(canonical));
    const entries = ownership.get(state) || [];
    const counts = new Map();
    for (const e of entries) counts.set(e.province, (counts.get(e.province) || 0) + 1);
    const missing = [...expected].filter(p => !counts.has(p)).sort();
    const extra = [...counts.keys()].filter(p => !expected.has(p)).sort();
    const duplicate = [...counts].filter(([, count]) => count > 1).map(([p]) => p).sort();
    if (missing.length || extra.length || duplicate.length) issues.push({ state, owners: [...new Set(entries.map(e => e.owner))].sort(), missing, extra, duplicate });
  }
  const obsoleteStates = [...ownership.keys()].filter(s => !regions.has(s));
  return { landStates: regions.size, assignedProvinces: [...ownership.values()].reduce((sum, es) => sum + es.length, 0), issues, obsoleteStates };
}

if (require.main === module) {
  const result = audit();
  if (process.argv.includes('--json')) console.log(JSON.stringify(result, null, 2));
  else {
    for (const issue of result.issues) console.log(JSON.stringify(issue));
    console.log(`${result.landStates} land states; ${result.assignedProvinces} assignments; ${result.issues.length} states with gaps, invalid provinces or duplicates; ${result.obsoleteStates.length} obsolete states.`);
    for (const s of result.obsoleteStates) console.log(`Obsolete state: ${s}`);
  }
  process.exitCode = result.issues.length || result.obsoleteStates.length ? 1 : 0;
}
module.exports = { audit, parse, children, scalar, words, canonical, read, files, root, base };

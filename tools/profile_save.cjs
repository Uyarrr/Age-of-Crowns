/** Read-only counts from an uncompressed Victoria 3 debug save.
 * node tools/profile_save.cjs "C:/path/to/save.v3" [another-save.v3 ...]
 * Compare saves from the same playthrough and mod revision before drawing conclusions.
 */
const fs = require('node:fs');
const assert = require('node:assert/strict');

function profile(file) {
  const text = fs.readFileSync(file, 'utf8');
  assert(text.startsWith('SAV') && text.includes('\nmeta_data={'), 'Requires an uncompressed text/debug save');
  function section(start, end) {
    const first = text.indexOf(`\n${start}={`);
    const last = text.indexOf(`\n${end}={` , first + 1);
    assert(first >= 0 && last > first, `Missing save sections: ${start}/${end}`);
    return text.slice(first, last);
  }
  const count = (s, regex) => [...s.matchAll(regex)].length;
  const pops = section('pops', 'country_manager');
  const countries = section('country_manager', 'states');
  const buildings = section('building_manager', 'building_ownership_manager');
  const markets = section('market_manager', 'technology');
  const types = {};
  for (const match of buildings.matchAll(/^\tbuilding=(\S+)/gm)) {
    types[match[1]] = (types[match[1]] || 0) + 1;
  }
  return {
    file,
    date: text.match(/^date=(.+)/m)?.[1],
    playthrough: text.match(/^playthrough_id="([^"]+)"/m)?.[1],
    popGroups: count(pops, /^\ttype=/gm),
    countryRecords: count(countries, /^\tdefinition=/gm),
    countriesWithMarket: count(countries, /^\tmarket=/gm),
    marketRecords: count(markets, /^\towner=/gm),
    stateRecords: count(section('states', 'interest_groups'), /^\tcapital=/gm),
    buildingRecords: Object.values(types).reduce((sum, n) => sum + n, 0),
    buildingsByType: types,
  };
}
if (require.main === module) {
  assert(process.argv.length > 2, 'Usage: node tools/profile_save.cjs path/to/debug-save.v3 [...]');
  for (const file of process.argv.slice(2)) console.log(JSON.stringify(profile(file), null, 2));
}
module.exports = { profile };

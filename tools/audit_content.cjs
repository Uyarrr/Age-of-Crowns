/** Audit every local English file and all live journals/events/buttons.
 * node tools/audit_content.cjs
 */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const a=require('./audit_map_ownership.cjs');
function parse(text,file){
 const tokens=[...text.matchAll(/#[^\r\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>!?"#]+/g)].map(m=>m[0]).filter(t=>!t.startsWith('#'));
 let i=0;
 function atom(){const t=tokens[i++];assert(t!==undefined&&t!=='}',`${file}: missing value`);return t.startsWith('"')?JSON.parse(t):t;}
 function block(nested=false){
  const out=[];
  while(i<tokens.length&&tokens[i]!=='}'){
   const key=atom();assert(key!=='{',`${file}: unexpected brace`);
   if(['=','?=','>=','<=','!=','>','<'].includes(tokens[i])){
    const op=tokens[i++];let value;
    if(tokens[i]==='{'){i++;value=block(true);}else value=atom();
    out.push({key,op,value});
   }else out.push({key});
  }
  if(nested)assert.equal(tokens[i++],'}',`${file}: unclosed block`);
  return out;
 }
 const result=block();assert.equal(i,tokens.length,`${file}: unmatched brace`);return result;
}
const walk=(nodes,fn,parents=[])=>{for(const n of nodes){fn(n,parents);if(Array.isArray(n.value))walk(n.value,fn,[...parents,n.key]);}};
const one=(nodes,key)=>{const n=nodes.find(n=>n.key===key);assert(n,`Missing ${key}`);return n;};
const recursive=dir=>fs.existsSync(dir)?fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?recursive(path.join(dir,e.name)):[path.join(dir,e.name)]):[];
function audit(){
 const english=new Map(),localKeys=new Set(),duplicates=new Set();let englishFiles=0,entries=0;
 for(const dir of [path.join(a.base,'localization/english'),path.join(a.root,'localization/english')])for(const p of recursive(dir).filter(p=>p.endsWith('.yml'))){
  const local=p.startsWith(a.root),text=a.read(p);if(local){englishFiles++;assert(text.startsWith('l_english:'),`BDE language header: ${p}`);}
  for(const [i,line]of text.split(/\r?\n/).entries()){
   if(!line.trim()||line.trim().startsWith('#')||line==='l_english:')continue;
   const m=line.match(/^\s*([^#\s:]+):\d*\s+"(.*)"\s*(?:#.*)?$/);
   if(local)assert(m,`${p}:${i+1}: malformed localization`);
   if(!m)continue;
   english.set(m[1],m[2]);
   if(local){entries++;if(localKeys.has(m[1]))duplicates.add(m[1]);localKeys.add(m[1]);}
  }
 }
 const dirs=['common/journal_entries','events','common/scripted_buttons','common/scripted_progress_bars'];
 const trees=new Map(),symbols=new Map();
 for(const dir of [...dirs,'common/scripted_effects','common/scripted_triggers','common/static_modifiers','common/technology/technologies']){
  const ids=new Set();
  const localFiles=a.files(path.join(a.root,dir));
  if(!['events','common/journal_entries'].includes(dir)){
   const overridden=new Set(localFiles.map(p=>path.basename(p)));
   const baseDir=path.join(a.base,dir);
   if(fs.existsSync(baseDir))for(const p of a.files(baseDir))if(!overridden.has(path.basename(p)))
    for(const m of a.read(p).matchAll(/^[ \t]*(?:\uFEFF)?([\w.]+)\s*=\s*\{/gm))ids.add(m[1]);
  }
  for(const p of localFiles){
   const nodes=parse(a.read(p),p);for(const n of nodes)ids.add(n.key);
   if(dirs.includes(dir))trees.set(p,nodes);
  }
  symbols.set(dir,ids);
 }
 let references=0;
 const refDirs={scripted_button:'common/scripted_buttons',scripted_progress_bar:'common/scripted_progress_bars',has_technology_researched:'common/technology/technologies',add_technology_researched:'common/technology/technologies'};
 for(const [p,nodes]of trees)walk(nodes,(n,parents)=>{
  if(typeof n.value!=='string')return;
  if(refDirs[n.key]){assert(symbols.get(refDirs[n.key]).has(n.value),`Undefined ${n.key}: ${n.value} (${p})`);references++;}
  if(n.key==='id'&&parents.at(-1)==='trigger_event'){assert(symbols.get('events').has(n.value),`Missing event ${n.value} (${p})`);references++;}
  const localized=['title','desc','flavor','text','header','effect_header','conclusion_desc'].includes(n.key)||n.key==='name'&&parents.at(-1)==='option';
  if(localized&&/^[\w.]+$/.test(n.value)&&!['yes','no'].includes(n.value)){
   assert(english.has(n.value),`Missing English ${n.value} (${path.basename(p)})`);references++;
  }
  if(['icon','texture'].includes(n.key)&&n.value.startsWith('gfx/'))assert(fs.existsSync(path.join(a.root,n.value))||fs.existsSync(path.join(a.base,n.value)),`Missing asset ${n.value}`);
 });
 for(const dir of ['common/journal_entries','events'])for(const p of a.files(path.join(a.root,dir)))assert(!/\bgame_date\s*[<>=]/.test(a.read(p)),`Calendar gate remains: ${p}`);
 for(const p of a.files(path.join(a.root,'common/journal_entries')))for(const j of trees.get(p)){
  assert(!j.value.some(n=>['complete','fail','invalid','on_complete','on_fail','on_invalid','event_outcome_completed_desc','custom_completion_header'].includes(n.key)),`${j.key}: retired pre-1.15 journal field`);
  assert(j.value.some(n=>n.key==='activation_description'));
  for(const outcome of j.value.filter(n=>n.key==='outcome')){
   assert(one(outcome.value,'conclusion_desc'));
   assert(one(outcome.value,'trigger'));assert(one(outcome.value,'effect'));
  }
 }
 for(const [key,value]of english)if(/^(je_england_|je_aoc_england_|england_|england_overseas\.|national_colonization\.|colonial_administration_events\.)/.test(key)&&/(?:_reason|\.(?:desc|flavor|d|f))$/.test(key)){
  const count=value.replace(/\[[^\]]*\]/g,'scope').split(/\s+/).length;
  assert(count<=85,`Long live prose: ${key} (${count} words)`);
 }
 // Exercise the actual availability trigger against new and existing-save states.
 const button=one(trees.get(path.join(a.root,'common/scripted_buttons/zz_war_of_the_roses_buttons.txt')),'wotr_summon_great_council_button');
 function evaluate(nodes,state){return nodes.every(n=>{
  if(n.key==='text')return true;
  if(['custom_tooltip','AND'].includes(n.key))return evaluate(n.value,state);
  if(n.key==='NOT')return !evaluate(n.value,state);
  if(n.key==='OR')return n.value.some(x=>evaluate([x],state));
  if(n.key==='has_variable')return state.variables.has(n.value);
  if(n.key==='has_modifier')return state.modifiers.has(n.value);
  if(n.key==='has_journal_entry')return state.journals.has(n.value);
  if(n.key==='any_revolution_ongoing')return Boolean(state.revolution)===(n.value==='yes');
  if(n.key.startsWith('var:')){
   const left=state.values[n.key.slice(4)]??0,right=Number(n.value);
   return {'=':left===right,'>=':left>=right,'<=':left<=right,'>':left>right,'<':left<right,'!=':left!==right}[n.op];
  }
  throw Error(`Unhandled council trigger ${n.key}`);
 });}
 const state={variables:new Set(),modifiers:new Set(),journals:new Set(['je_england_2'])};
 const possible=one(button.value,'possible').value;
 assert(evaluate(possible,state));
 state.modifiers.add('war_of_the_roses_great_council');assert(!evaluate(possible,state),'Existing council save can spam');
 state.modifiers.clear();state.variables.add('wotr_council_cooldown');assert(!evaluate(possible,state),'Cooldown can be bypassed');
 state.variables.clear();state.variables.add('wotr_civil_war_active');assert(!evaluate(possible,state),'Council during civil war');
 state.variables.clear();assert(evaluate(possible,state));
 const effect=one(button.value,'effect').value;
 const cooldown=effect.find(n=>n.key==='set_variable'&&one(n.value,'name').value==='wotr_council_cooldown');
 assert.equal(one(cooldown.value,'months').value,'48');
 const england=trees.get(path.join(a.root,'common/journal_entries/england.txt'));
 const hyw=one(england,'je_england_1');
 const outcomes=hyw.value.filter(n=>n.key==='outcome');
 assert.equal(one(one(one(outcomes[0].value,'effect').value,'trigger_event').value,'id').value,'england.300');
 assert.equal(one(one(one(outcomes[1].value,'effect').value,'trigger_event').value,'id').value,'england.301');
 const lost=one(outcomes[1].value,'trigger').value;assert(lost.some(n=>n.key==='NOT'),'Zero possessions must fail');
 const roses=one(england,'je_england_2');
 const monthly=one(one(roses.value,'on_monthly_pulse').value,'effect').value;
 function timerRule(name){return monthly.find(n=>n.key==='if'&&n.value.some(c=>c.key==='change_variable'&&one(c.value,'name').value===name));}
 const stable=timerRule('wotr_stability_months_var'),peaceful=timerRule('wotr_peaceful_months_var');
 assert(stable&&peaceful);
 const realm={variables:new Set(['wotr_dynasty_lancaster']),modifiers:new Set(),journals:new Set(['je_england_2']),values:{wotr_wars_fought_var:1,war_of_roses_tension_current_var:30,war_of_roses_balance_current_var:65,wotr_phase_var:2}};
 let months=0;
 for(let i=0;i<24;i++)months=evaluate(one(stable.value,'limit').value,realm)?months+1:0;
 assert.equal(months,24);
 realm.values.war_of_roses_tension_current_var=31;assert(!evaluate(one(stable.value,'limit').value,realm));
 realm.values.war_of_roses_tension_current_var=30;realm.variables.add('wotr_civil_war_active');assert(!evaluate(one(stable.value,'limit').value,realm));
 realm.variables.delete('wotr_civil_war_active');realm.variables.delete('wotr_dynasty_lancaster');realm.variables.add('wotr_dynasty_york');realm.values.war_of_roses_balance_current_var=35;
 assert(evaluate(one(stable.value,'limit').value,realm));
 realm.variables.delete('wotr_dynasty_york');realm.variables.add('wotr_dynasty_lancaster');realm.values.wotr_wars_fought_var=0;realm.values.war_of_roses_balance_current_var=65;realm.values.war_of_roses_tension_current_var=20;
 assert(evaluate(one(peaceful.value,'limit').value,realm));realm.values.wotr_phase_var=1;assert(!evaluate(one(peaceful.value,'limit').value,realm));
 console.log(`PASS: ${englishFiles} English files, ${entries} local entries; ${duplicates.size} duplicate keys tracked across localization overrides.`);
 console.log(`PASS: ${trees.size} journal/event/button/bar files; ${references} localization, technology and event references; referenced assets exist; no journal/event calendar gates.`);
 console.log('PASS: council availability, cooldown and civil war; both dynasties’ stability boundaries, peaceful phase gate, Hundred Years War outcomes, and live narrative length limits.');
}
if(require.main===module)audit();
module.exports={parse,walk,one};

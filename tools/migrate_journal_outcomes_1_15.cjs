/** Idempotent migration to the installed 1.15 journal outcome schema.
 * Reference: game/common/journal_entries/journal_entries.md.
 */
const fs=require('node:fs'),path=require('node:path');
const a=require('./audit_map_ownership.cjs');
const body=(text,n)=>n?text.slice(n.start,n.end).slice(text.slice(n.start,n.end).indexOf('{')+1,-1).trim():'';
const conclusions=[];
for(const p of a.files(path.join(a.root,'common/journal_entries'))){
 const text=a.read(p),edits=[];
 for(const journal of a.parse(text)){
  const nodes=journal.value;
  if(!Array.isArray(nodes))continue;
  const get=k=>nodes.find(n=>n.key===k);
  if(!get('activation_description'))edits.push({start:journal.end-1,end:journal.end-1,text:'\n\tactivation_description = { always = yes }\n'});
  for(const [condition,effect,desc,kind]of [
   ['complete','on_complete','event_outcome_completed_desc','completion'],
   ['fail','on_fail','event_outcome_failed_desc','failure'],
   ['invalid','on_invalid',null,'invalid']]){
   const trigger=get(condition),action=get(effect),description=desc?get(desc):null;
   const old=[trigger,action,description].filter(Boolean);
   if(!old.length)continue;
   const triggerBody=body(text,trigger);
   let replacement='';
   if(triggerBody){
    const conclusion=kind==='completion'?journal.key+'_completed_desc':'je_standard_failure_conclusion_desc';
    const header=get('custom_completion_header');
    replacement='outcome = {\n';
    if(kind==='invalid')replacement+='\t\tflags = { hidden invalid_outcome }\n';
    else replacement+=`\t\theader = ${kind==='completion'&&header?header.value:'je_standard_'+kind+'_header'}\n\t\teffect_header = je_standard_on_${kind}_header\n\t\tcolor = "${kind==='completion'?'gold_positive':'blue_negative'}"\n`;
    replacement+=`\t\tconclusion_desc = ${conclusion}\n\t\ttrigger = {\n${triggerBody}\n\t\t}\n\t\teffect = {\n${body(text,action)}\n\t\t}\n`;
    if(body(text,description))replacement+='\t\tevent_outcome_desc = {\n'+body(text,description)+'\n\t\t}\n';
    replacement+='\t}';
    if(kind==='completion')conclusions.push(journal.key);
   }
   for(const [i,n]of old.entries())edits.push({start:n.start,end:n.end,text:i===0?replacement:''});
  }
  if(get('custom_completion_header'))edits.push({...get('custom_completion_header'),text:''});
 }
 if(edits.length){
  const bom=fs.readFileSync(p).subarray(0,3).equals(Buffer.from([239,187,191]));
  const result=edits.sort((a,b)=>b.start-a.start).reduce((s,e)=>s.slice(0,e.start)+e.text+s.slice(e.end),text);
  fs.writeFileSync(p,(bom?'\uFEFF':'')+result);
 }
}
if(conclusions.length){
 const copy={
  je_england_1:'The Crown has secured its position in France.',
  je_england_2:'The dynastic struggle has reached a lasting settlement.',
  je_england_3:'The British Isles have been brought under one government.',
  je_earn_recognition:'The great powers have accepted our diplomatic standing.',
  je_warlord_china:'Sustained order has restored confidence in the Ming government.',
  je_aoc_england_cape:'The Cape now supports a lasting colonial economy.',
  je_aoc_england_east_india:'The Company has established three Indian possessions.',
  je_aoc_england_australasia:'Australia and New Zealand have developed under separate colonial governments.',
  je_aoc_england_hudson_bay:'The Company’s inland posts sustain a productive fur trade.',
  je_aoc_england_royal_navy:'A decade of naval readiness has secured our overseas routes.',
  je_aoc_england_new_world:'Our American territories support a substantial Atlantic empire.'
 };
 const loc=path.join(a.root,'localization/english/aoc_journal_outcomes_l_english.yml');
 fs.writeFileSync(loc,'\uFEFFl_english:\n'+conclusions.map(k=>` ${k}_completed_desc: "${copy[k]||'The undertaking has been completed.'}"`).join('\n')+'\n');
}

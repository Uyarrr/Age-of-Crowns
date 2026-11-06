/** Verify population, province, startup and research invariants. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const a=require('./audit_map_ownership.cjs');
const data=JSON.parse(a.read(path.join(a.root,'docs/south_america_1444.json')));
const owners={},population={},countryPopulation={},acceptedPopulation={},buildingRows=[];
const defs=new Map();
for(const p of a.files(path.join(a.root,'common/country_definitions'))){
 const text=a.read(p);
 for(const n of a.parse(text)){
  const tag=n.key.replace('REPLACE:','');
  if(defs.has(tag)&&/^\w+\s*\?=/.test(text.slice(n.start,n.end)))continue;
  assert(!defs.has(tag)||!Object.hasOwn(data.profiles,tag),`Duplicate playable definition: ${tag}`);
  defs.set(tag,n);
 }
}
for(const p of a.files(path.join(a.root,'common/history/states')))for(const top of a.parse(a.read(p)))for(const s of top.value||[]){
 const state=s.key.slice(2);if(!data.finalOwners[state])continue;
 for(const c of a.children(s,'create_state')){
  const tag=a.scalar(c,'country').slice(2);owners[state]??={};
  assert(!owners[state][tag],`Repeated owner: ${state} ${tag}`);
  owners[state][tag]=a.words(c,'owned_provinces').sort();
  if(tag in data.profiles)assert.equal(a.scalar(c,'state_type'),'incorporated');
 }
}
assert.deepEqual(owners,data.finalOwners,'Ownership differs from reviewed cores');
for(const [state,olds]of Object.entries(data.oldOwners))assert.deepEqual(Object.values(owners[state]).flat().sort(),Object.values(olds).flat().sort(),`Province coverage changed: ${state}`);
for(const [key,provs]of Object.entries(data.baseline.andineOwners)){
 const [state,tag]=key.split('|');assert.deepEqual(owners[state][tag].map(a.canonical).sort(),provs,`Andean territory changed: ${key}`);
}
for(const folder of ['pops','buildings'])for(const p of a.files(path.join(a.root,'common/history',folder))){
 const text=a.read(p);
 for(const top of a.parse(text))for(const s of top.value||[]){
  const state=s.key.slice(2);if(!owners[state])continue;
  for(const r of s.value||[]){
   const tag=r.key.replace('region_state:','');
   if(r.value?.length)assert(owners[state][tag],`Orphan ${folder}: ${state} ${tag}`);
   for(const n of r.value||[]){
    if(folder==='pops'&&n.key==='create_pop'){
     const size=Number(a.scalar(n,'size')),culture=a.scalar(n,'culture');
     assert(Number.isInteger(size)&&size>0);
     const id=[state,culture,a.scalar(n,'religion'),a.scalar(n,'pop_type')].join('|');
     population[id]=(population[id]||0)+size;countryPopulation[tag]=(countryPopulation[tag]||0)+size;
     if(a.words(defs.get(tag),'cultures').includes(culture))acceptedPopulation[tag]=(acceptedPopulation[tag]||0)+size;
    }else if(folder==='buildings')buildingRows.push({state,raw:text.slice(n.start,n.end).replace(/\s+/g,' ')});
   }
  }
 }
}
assert.deepEqual(population,data.baseline.population,'State/culture/religion/type population changed');
assert.deepEqual(buildingRows,data.baseline.buildings,'Starting buildings changed');
const active=new Set(Object.values(owners).flatMap(Object.keys));
assert.deepEqual([...active].sort(),data.activeAfter);
assert.deepEqual([...active].filter(t=>a.scalar(defs.get(t),'country_type')==='decentralized'),['AMZ']);
const history=a.parse(a.read(path.join(a.root,'common/history/countries/aoc_south_america.txt')))[0];
const laws=new Set(a.files(path.join(a.root,'common/laws')).flatMap(p=>a.parse(a.read(p)).map(n=>n.key)));
const techs=new Set(a.files(path.join(a.root,'common/technology/technologies')).flatMap(p=>a.parse(a.read(p)).map(n=>n.key)));
for(const [tag,f]of Object.entries(data.profiles)){
 const d=defs.get(tag),capital=a.scalar(d,'capital');
 assert.equal(a.scalar(d,'country_type'),'unrecognized');assert(owners[capital]?.[tag],`Unowned capital ${tag}`);
 assert.equal(capital,'STATE_'+f.capital);assert(f.sources.length&&f.confidence);
 const count=Object.values(owners).reduce((n,s)=>n+(s[tag]?.length||0),0);
 const adjacency=data.coreAdjacency[tag],reached=new Set(),queue=[Object.keys(adjacency)[0]];
 while(queue.length){const p=queue.pop();if(reached.has(p))continue;reached.add(p);queue.push(...adjacency[p].filter(n=>!reached.has(n)));}
 assert.equal(reached.size,count,`Disconnected core ${tag}`);
 assert(count>=3&&count<=12,`Core too large/small ${tag}`);
 assert(countryPopulation[tag]>=12000,`Unviable population ${tag}`);
 assert(acceptedPopulation[tag]/countryPopulation[tag]>=0.5,`No local primary-culture majority ${tag}`);
 const h=a.children(history,'c:'+tag)[0];assert(h,`Missing startup ${tag}`);
 for(const n of a.children(h,'activate_law'))assert(laws.has(n.value.slice(9)),`Undefined law ${n.value}`);
 for(const n of a.children(h,'add_technology_researched'))assert(techs.has(n.value),`Undefined technology ${n.value}`);
 assert(a.children(h,'add_technology_researched').some(n=>n.value==='peasant_levy'));
}
const coverage=a.audit();assert.equal(coverage.issues.length,0);assert.equal(coverage.obsoleteStates.length,0);
console.log(`PASS: ${Object.keys(owners).length} South American regions, ${Object.values(owners).flatMap(Object.values).flat().length} provinces, ${Object.keys(data.profiles).length} compact playable cores; one decentralized owner.`);
console.log(`PASS: ${Object.values(population).reduce((a,b)=>a+b,0)} people conserved by state/culture/religion/type; ${buildingRows.length} building configurations preserved; all Andean playable territory retained.`);
console.log('PASS: owned capitals, local primary-culture majorities, >=12,000 inhabitants, valid founding laws and technologies.');

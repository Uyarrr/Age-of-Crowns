"""Audit Age of Crowns using only common/goods/uyr_goods.txt prices.

Run with Python 3: python tools/economy_audit.py
"""
from pathlib import Path
import re
import json
import itertools
import csv
import sys
import os
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('VICTORIA3_GAME_DIR',r'C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game'))
TOKEN = re.compile(r'#[^\n]*|"[^"\\]*(?:\\.[^"\\]*)*"|[{}=]|[^\s{}=#]+')

class Node:
    def __init__(self, key, value, start, end):
        self.key, self.value, self.start, self.end = key, value, start, end
    def children(self, key):
        return [n for n in self.value if n.key == key] if isinstance(self.value, list) else []
    def child(self, key):
        return next(iter(self.children(key)), None)
    def scalar(self, key, default=None):
        n = self.child(key)
        return n.value if n else default
    def words(self, key):
        n = self.child(key)
        return [c.key for c in n.value] if n and isinstance(n.value, list) else []

def parse(text):
    ts = [m for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    def block(i, nested=False):
        result = []
        while i < len(ts) and ts[i].group() != '}':
            k = ts[i]; i += 1
            if i < len(ts) and ts[i].group() == '=':
                i += 1
                if ts[i].group() == '{':
                    v, i = block(i + 1, True)
                    end = ts[i - 1].end()
                else:
                    v = ts[i].group(); end = ts[i].end(); i += 1
            else:
                v = None; end = k.end()
            result.append(Node(k.group(), v, k.start(), end))
        if nested:
            if i == len(ts):
                raise ValueError('Unclosed block')
            i += 1
        return result, i
    nodes, i = block(0)
    if i != len(ts):
        raise ValueError('Unexpected closing brace')
    return nodes

def load(folder, inherited=False):
    result, paths, duplicates = {}, {}, []
    local_paths=sorted((ROOT / 'common' / folder).glob('*.txt'))
    replaced={p.name for p in local_paths}
    base_paths = [p for p in sorted((BASE / 'common' / folder).glob('*.txt')) if p.name not in replaced] if inherited else []
    for path in base_paths + local_paths:
        for n in parse(path.read_text(encoding='utf-8-sig')):
            if n.key in result and path.is_relative_to(ROOT) and paths[n.key].is_relative_to(ROOT):
                duplicates.append(n.key)
            result[n.key] = n
            paths[n.key] = path
    return result, paths, duplicates

def goods(pm):
    result = []
    bm = pm.child('building_modifiers')
    if bm:
        for scale in bm.value:
            if isinstance(scale.value, list):
                for n in scale.value:
                    m = re.fullmatch(r'goods_(input|output)_(.+)_add', n.key)
                    if m:
                        result.append((m[1], m[2], float(n.value), scale.key, n))
    return result

def values(pm, prices):
    inp = out = 0
    for kind, g, qty, _, _ in goods(pm):
        if g in prices:
            if kind == 'input': inp += qty * prices[g]
            else: out += qty * prices[g]
    return inp, out, out - inp

EXCLUDED = {'building_rubber_plantation','building_whaling_station','building_oil_rig','building_sulfur_mine'}

def custom_path(path):
    return path.is_relative_to(ROOT) and not re.match(r'^\d+_',path.name)

def sector_of(building):
    group=building.scalar('building_group')
    if building.key=='building_village':return 'cottage'
    if group in {'bg_agriculture','bg_staple_crops','bg_ranching','bg_plantations'}:return 'agriculture'
    if group in {'bg_heavy_industry','bg_military_industry','bg_ship_construction'}:return 'heavy_industry'
    if group=='bg_light_industry':return 'light_industry'
    if group in {'bg_mining','bg_logging','bg_fishing','bg_gold_fields'}:return 'resource'
    return 'other'

def sector_combinations(buildings,groups,pms,paths,prices,weights):
    """Latest production recipes at the same age and baseline capacity.

    Assume access to all technologies through that era; include every
    available secondary choice. General audits still test all combinations.
    """
    rows=[]
    techs,_,_=load('technology/technologies',True)
    def available(n,age):
        required=n.words('unlocking_technologies')+n.words('unlocking_global_technologies')
        for key in required:
            if key not in techs:return False
            era=techs[key].scalar('era','era_1')
            if int(era.rsplit('_',1)[-1])>age:return False
        return True
    for key,b in buildings.items():
        sector=sector_of(b)
        if sector not in {'agriculture','light_industry','heavy_industry'}:continue
        bgs=b.words('production_method_groups')
        if not bgs or bgs[0] not in groups:continue
        primary=[k for k in groups[bgs[0]].words('production_methods') if k in pms and custom_path(paths[k]) and any(kind=='output' and q>0 for kind,g,q,s,n in goods(pms[k]))]
        if not primary:continue
        for age in range(1,7):
            unlocked=[k for k in primary if available(pms[k],age)]
            if not unlocked or not available(b,age):continue
            choices=[[unlocked[-1]]]+[[k for k in groups[g].words('production_methods') if k in pms and available(pms[k],age)] for g in bgs[1:] if g in groups]
            if any(not seq for seq in choices):continue
            for combo in itertools.product(*choices):
                if any(not set(pms[k].words('unlocking_production_methods')).issubset(combo) for k in combo):continue
                staff=sum(workers(pms[k]) for k in combo)
                if staff<=0:continue
                inp=sum(values(pms[k],prices)[0] for k in combo)
                out=sum(values(pms[k],prices)[1] for k in combo)
                pay=sum(wage_units(pms[k],weights) for k in combo)*5/52
                capacity=workers(pms[combo[0]])
                if capacity<=0:continue
                net=out-inp-pay
                rows.append(dict(building=key,sector=sector,age=age,tier=primary.index(combo[0])+1,primary=combo[0],workers=staff,reference_capacity=capacity,inputs=inp,outputs=out,payroll=pay,profit=net,profit_per_3000=net*3000/capacity))
    return rows

def is_alternative(group):
    return any(s in group for s in ('village','subsistence','serfdom','exploitation','working_conditions','ownership'))

def workers(pm):
    bm=pm.child('building_modifiers')
    return sum(float(n.value) for s in bm.value if isinstance(s.value,list) for n in s.value if re.fullmatch(r'building_employment_\w+_add',n.key)) if bm else 0

def wage_units(pm, weights):
    bm=pm.child('building_modifiers')
    return sum(float(n.value)*weights.get(n.key[len('building_employment_'):-len('_add')],1) for s in bm.value if isinstance(s.value,list) for n in s.value if re.fullmatch(r'building_employment_\w+_add',n.key)) if bm else 0

def wage_weights():
    weights={}
    for folder in [BASE,ROOT]:
        for path in (folder/'common/pop_types').glob('*.txt'):
            text=path.read_text(encoding='utf-8-sig')
            key=re.search(r'^\s*(\w+)\s*=\s*\{',text)
            wage=re.search(r'\bwage_weight\s*=\s*([\d.]+)',text)
            if key and wage:weights[key[1]]=0 if re.search(r'(paid_private_wage\s*=\s*no|subsistence_income\s*=\s*yes)',text) else float(wage[1])
    return weights

def csvfile(path, rows):
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

PUBLIC_BENEFITS={
    'pmg_building_construction_sector_main':'country_construction_add',
    'pmg_building_chancery_main':'country_bureaucracy_add',
    'pmg_building_hospital_main':'country_weekly_innovation_add',
    'pmg_building_university_main':'country_weekly_innovation_add',
    'pmg_building_tax_office_main':'state_tax_capacity_add',
    'pmg_building_chancery_silver':'state_tax_capacity_add',
    'pmg_building_chancery_gold':'state_tax_capacity_add',
    'pmg_building_trade_center_trade_quantity':'state_trade_quantity_mult',
    'pmg_base_building_naval_fortification':'state_fortification_naval_invasion_add',
}

def benefit_value(node,key):
    if not isinstance(node.value,list):return 0
    return sum(float(c.value) if c.key==key and not isinstance(c.value,list) else benefit_value(c,key) for c in node.value)

def main():
    prices = {n.key: float(n.scalar('cost')) for n in parse((ROOT/'common/goods/uyr_goods.txt').read_text(encoding='utf-8-sig'))}
    pms, pp, dp = load('production_methods', True)
    groups, gp, dg = load('production_method_groups', True)
    buildings, bp, db = load('buildings')
    techs, _, _ = load('technology/technologies', True)
    weights=wage_weights()
    excluded = {k for k,b in buildings.items() if b.scalar('buildable') == 'no' and k in EXCLUDED}
    used_groups = {g for k,b in buildings.items() if k not in excluded for g in b.words('production_method_groups')}
    used_pms = {p for g in used_groups if g in groups for p in groups[g].words('production_methods')}
    protected_warnings={}
    custom_pms={p for p in used_pms & pms.keys() if custom_path(pp[p])}
    protected_warnings['missing_methods'] = sorted(p for p in used_pms-pms.keys() if not any(custom_path(gp[g]) and p in groups[g].words('production_methods') for g in used_groups & groups.keys()))
    missing_groups = sorted(used_groups - groups.keys())
    missing_pms = sorted(used_pms - pms.keys()-set(protected_warnings['missing_methods']))
    unknown_all = [(p, g) for p in sorted(used_pms & pms.keys()) for _, g, _, _, _ in goods(pms[p]) if g not in prices]
    unknown=[x for x in unknown_all if x[0] in custom_pms]
    protected_warnings['unsupported_goods']=[x for x in unknown_all if x[0] not in custom_pms]
    losses = [(p, *values(pms[p], prices)) for p in sorted(custom_pms) if any(k=='output' and q>0 for k,g,q,s,n in goods(pms[p])) and values(pms[p], prices)[2] <= 0]
    fractional=[(p,g,q) for p in sorted(custom_pms) for k,g,q,s,n in goods(pms[p]) if not q.is_integer()]
    unrounded_outputs=[]
    for path in (ROOT/'common/production_methods').glob('*.txt'):
        if not custom_path(path):continue
        for n in parse(path.read_text(encoding='utf-8-sig')):
            unrounded_outputs.extend((n.key,g,q) for kind,g,q,s,v in goods(n) if kind=='output' and q%5!=0)
    regressions = []
    wage_regressions=[]
    for g in sorted(used_groups & groups.keys()):
        if is_alternative(g):continue
        seq = [p for p in groups[g].words('production_methods') if p in custom_pms]
        seq = [p for p in seq if any(k=='output' and q>0 for k,_,q,_,_ in goods(pms[p]))]
        for a,b in zip(seq,seq[1:]):
            if values(pms[b],prices)[2] <= values(pms[a],prices)[2]:
                regressions.append((g,a,b,values(pms[a],prices)[2], values(pms[b],prices)[2]))
            neta=values(pms[a],prices)[2]-wage_units(pms[a],weights)*5/52
            netb=values(pms[b],prices)[2]-wage_units(pms[b],weights)*5/52
            if netb<=neta:wage_regressions.append((g,a,b,round(neta,3),round(netb,3)))
    produced = {g for p in used_pms & pms.keys() for k,g,q,_,_ in goods(pms[p]) if k=='output' and q>0}
    consumed = {g for p in used_pms & pms.keys() for k,g,q,_,_ in goods(pms[p]) if k=='input' and q>0}
    # Army, mobilization and ship demand are real sinks too.
    military_consumed=set()
    for folder in ['combat_unit_types','mobilization_options','ship_types','ship_modifications']:
        for path in (ROOT/'common'/folder).glob('*.txt'):
            military_consumed.update(re.findall(r'goods_input_(\w+)_add\s*=',re.sub(r'#[^\n]*','',path.read_text(encoding='utf-8-sig'))))
    needs,_,_ = load('pop_needs')
    popgoods = {e.scalar('goods') for n in needs.values() for e in n.children('entry')}
    required_unknown=[(p,n.value) for p in sorted(custom_pms) for n in pms[p].children('required_input_goods') if n.value not in prices]
    need_errors=[]
    for k,n in needs.items():
        entries=n.children('entry')
        gs=[e.scalar('goods') for e in entries]
        if n.scalar('default') not in gs:need_errors.append((k,'default is not a substitute'))
        for e in entries:
            lo=float(e.scalar('min_supply_share',0));hi=float(e.scalar('max_supply_share',1))
            if not 0<=lo<=hi<=1:need_errors.append((k,e.scalar('goods'),'invalid shares'))
            if e.scalar('goods') not in prices:need_errors.append((k,e.scalar('goods'),'unsupported good'))
    packages,_,_=load('buy_packages')
    package_rows=[];last=0
    for key,n in packages.items():
        items=n.child('goods')
        total=sum(float(x.value) for x in items.value)
        if total<=last:need_errors.append((key,'budget does not rise with wealth'))
        last=total
        for x in items.value:
            if x.key not in needs:need_errors.append((key,x.key,'undefined need'))
        package_rows.append(dict(wealth=key,budget=total,seasonings=float(items.scalar('popneed_seasonings',0)),seasoning_share=round(float(items.scalar('popneed_seasonings',0))/total,4)))
    combination_errors=[];building_rows=[];combination_count=0;wage_stress_diagnostics=[]
    for key,b in buildings.items():
        if key in excluded:
            building_rows.append(dict(building=key,category='disabled outside goods list',combinations=0,min_margin='',max_margin='',min_stressed_margin='',min_workers='',min_stressed_profit_at_annual_wage_5='',min_break_even_annual_wage=''))
            continue
        choices=[groups[g].words('production_methods') for g in b.words('production_method_groups') if g in groups]
        choices=[seq for seq in choices if seq]
        has_saleable=any(any(kind=='output' and qty>0 for kind,g,qty,s,n in goods(pms[p])) for seq in choices for p in seq if p in pms)
        margins=[];stresses=[];staff=[];net_profits=[];break_even=[];count=0
        for combo in itertools.product(*choices):
            if any(p not in pms for p in combo):continue
            # PM dependencies are conjunctions; impossible combinations are skipped.
            if any(not set(pms[p].words('unlocking_production_methods')).issubset(combo) for p in combo):continue
            count+=1;combination_count+=1
            custom_combo=bool(set(combo)&custom_pms)
            ins=Counter();outs=Counter()
            for p in combo:
                for kind,g,qty,s,n in goods(pms[p]):
                    if g in prices:(ins if kind=='input' else outs)[g]+=qty
            if custom_combo and any(q<-0.001 for q in outs.values()):
                combination_errors.append((key,'negative output',combo,{g:q for g,q in outs.items() if q<0}))
            i=sum(q*prices[g] for g,q in ins.items());o=sum(q*prices[g] for g,q in outs.items())
            margin=o-i;stress=0.85*o-1.15*i
            emp=sum(workers(pms[p]) for p in combo)
            wu=sum(wage_units(pms[p],weights) for p in combo)
            net=stress-wu*5/52
            if custom_combo and emp<0:combination_errors.append((key,'negative workforce',combo,emp))
            if custom_combo and has_saleable and o>0 and margin<=0:combination_errors.append((key,'nonpositive margin',combo,margin))
            if custom_combo and has_saleable and o>0 and stress<=0:combination_errors.append((key,'nonpositive stressed margin',combo,round(stress,3)))
            if custom_combo and has_saleable and o>0 and net<=0:wage_stress_diagnostics.append((key,combo,round(net,3)))
            margins.append(margin);stresses.append(stress);staff.append(emp)
            net_profits.append(net)
            if wu>0:break_even.append(stress*52/wu)
        building_rows.append(dict(building=key,category='saleable' if has_saleable else 'public benefit / ownership',combinations=count,min_margin=round(min(margins),3) if margins else '',max_margin=round(max(margins),3) if margins else '',min_stressed_margin=round(min(stresses),3) if stresses else '',min_workers=min(staff) if staff else '',min_stressed_profit_at_annual_wage_5=round(min(net_profits),3) if net_profits else '',min_break_even_annual_wage=round(min(break_even),3) if break_even else ''))
    unknown_tech=[(p,t) for p in sorted(custom_pms) for t in pms[p].words('unlocking_technologies') if t not in techs]
    protected_warnings['missing_technologies']=[(p,t) for p in sorted((used_pms & pms.keys())-custom_pms) for t in pms[p].words('unlocking_technologies') if t not in techs]
    public_rows=[];public_errors=[]
    for group,benefit in PUBLIC_BENEFITS.items():
        previous=None
        for key in groups[group].words('production_methods'):
            if key not in custom_pms:continue
            pm=pms[key];amount=benefit_value(pm,benefit)
            if benefit=='state_trade_quantity_mult':amount+=1
            cost=values(pm,prices)[0]
            if not amount:continue
            unit=cost/amount
            public_rows.append(dict(group=group,pm=key,benefit=benefit,amount=amount,input_cost=cost,cost_per_benefit=round(unit,4)))
            if cost>0:
                if previous is not None and unit>=previous:public_errors.append((group,key,unit,previous))
                previous=unit
    summary = dict(goods=len(prices), buildings=len(buildings), excluded_disabled_buildings=sorted(excluded), groups=len(used_groups), pms=len(used_pms), combinations=combination_count, missing_groups=missing_groups, missing_pms=missing_pms, unknown_goods=unknown, unknown_required_goods=required_unknown, unknown_technologies=unknown_tech, losses=losses, regressions=regressions, wage_regressions_at_annual_wage_5=wage_regressions, combination_errors=combination_errors, pop_need_errors=need_errors, unproduced=sorted((consumed | popgoods)-produced), no_demand=sorted(produced-consumed-popgoods-military_consumed), duplicates=dict(pms=dp,groups=dg,buildings=db))
    summary['public_benefit_efficiency_errors']=public_errors
    summary['fractional_custom_recipe_quantities']=fractional
    summary['custom_pms']=len(custom_pms)
    summary['preserved_vanilla_warnings']=protected_warnings
    summary['wage_stress_diagnostics']=wage_stress_diagnostics
    summary['outputs_not_multiple_of_five']=unrounded_outputs
    sectors=sector_combinations(buildings,groups,pms,pp,prices,weights)
    sector_rows=[];sector_lookup={}
    for sector in ['agriculture','light_industry','heavy_industry']:
        for tier in sorted({r['age'] for r in sectors if r['sector']==sector}):
            selected=[r for r in sectors if r['sector']==sector and r['age']==tier]
            vals=[r['profit_per_3000'] for r in selected]
            sector_lookup[sector,tier]=(min(vals),max(vals))
            sector_rows.append(dict(sector=sector,age=tier,combinations=len(vals),min_profit_per_3000=round(min(vals),3),max_profit_per_3000=round(max(vals),3),mean_profit_per_3000=round(sum(vals)/len(vals),3)))
    sector_errors=[]
    for lower,higher in [('agriculture','light_industry'),('light_industry','heavy_industry')]:
        for tier in range(1,7):
            if (lower,tier) in sector_lookup and (higher,tier) in sector_lookup:
                ceiling=sector_lookup[lower,tier][1];floor=sector_lookup[higher,tier][0]
                if floor<ceiling+200-1e-6:sector_errors.append((lower,higher,tier,ceiling,floor))
    summary['sector_order_errors']=sector_errors
    protected_warnings['duplicate_groups']=[g for g in dg if not custom_path(gp[g]) or g=='pmg_base_building_railway']
    dg=[g for g in dg if g not in protected_warnings['duplicate_groups']]
    summary['duplicates']['groups']=dg
    summary['unproduced']=[g for g in summary['unproduced'] if g in prices]
    if '--write-report' in sys.argv:
        report=ROOT/'docs/economy';report.mkdir(parents=True,exist_ok=True)
        (report/'audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        csvfile(report/'buildings.csv',building_rows)
        csvfile(report/'pop_budgets.csv',package_rows)
        csvfile(report/'public_benefits.csv',public_rows)
        csvfile(report/'sector_profits.csv',sector_rows)
        csvfile(report/'sector_combinations.csv',[{k:round(v,3) if isinstance(v,float) else v for k,v in r.items()} for r in sectors])
        rows=[]
        for key in sorted(used_pms & pms.keys()):
            pm=pms[key];i,o,m=values(pm,prices)
            rows.append(dict(pm=key,file=pp[key].relative_to(ROOT).as_posix() if pp[key].is_relative_to(ROOT) else 'base_game/'+pp[key].relative_to(BASE).as_posix(),inputs=i,outputs=o,gross_margin=round(m,3),stressed_margin=round(o*.85-i*1.15,3),workers=workers(pm),technologies=' '.join(pm.words('unlocking_technologies')),recipe='; '.join(f'{kind} {g} {q:g}' for kind,g,q,s,n in goods(pm))))
        csvfile(report/'production_methods.csv',rows)
        csvfile(report/'goods.csv',[dict(good=g,base_price=prices[g],produced=g in produced,building_input=g in consumed,pop_need=g in popgoods,military_input=g in military_consumed) for g in prices])
    print(json.dumps(summary,indent=2))
    errors=missing_groups or missing_pms or unknown or required_unknown or unknown_tech or losses or regressions or wage_regressions or combination_errors or need_errors or public_errors or fractional or unrounded_outputs or sector_errors or dp or dg or db
    if errors: return 1
    return 0

if __name__ == '__main__': sys.exit(main())

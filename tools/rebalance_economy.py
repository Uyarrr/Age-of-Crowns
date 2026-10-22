"""Integer recipe authoring policy. Only custom, non-numbered PM files may change."""
import math
import re
import subprocess
import sys
import economy_audit as a

ROOT=a.ROOT
ORIGINALS={}

def five(q):
    return max(5,5*math.floor(q/5+.5)) if q>0 else (-five(-q) if q<0 else 0)

def write(path,text):
    raw=path.read_bytes() if path.exists() else b''
    bom=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') or path.suffix=='.yml' else b''
    newline='\r\n' if b'\r\n' in raw else '\n'
    text='\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n'
    path.write_bytes(bom+text.replace('\n',newline).encode())

def replace_node(text,key,fn):
    n=next(n for n in a.parse(text) if n.key==key)
    return text[:n.start]+fn(text[n.start:n.end])+text[n.end:]

def edit(path,fn):
    old=path.read_text(encoding='utf-8-sig');new=fn(old)
    if new!=old:write(path,new)

def upsert(path,snippets,header):
    text=path.read_text(encoding='utf-8-sig') if path.exists() else header+'\n'
    for snippet in snippets:
        key=a.parse(snippet)[0].key
        if any(n.key==key for n in a.parse(text)):text=replace_node(text,key,lambda _:snippet)
        else:text+='\n'+snippet+'\n'
    write(path,text)

def custom(path):
    return path.is_relative_to(ROOT) and not re.match(r'^\d+_',path.name)

def set_jobs(text,jobs):
    return re.sub(r'(building_employment_(\w+)_add\s*=\s*)(-?\d+)',lambda m:m[1]+str(jobs.get(m[2],int(m[3]))),text)

def balance_ports():
    # Ports provide public logistics as well as merchant marine. Keep their
    # staffing small enough for an early tax base to maintain them.
    jobs={
        1:{'laborers':300,'clerks':70,'bureaucrats':30},
        2:{'laborers':300,'machinists':80,'clerks':80,'bureaucrats':40},
        3:{'laborers':300,'machinists':120,'engineers':30,'clerks':100,'bureaucrats':50},
    }
    for building,filename,input_good in [('port','port_pm.txt','navalsupplies'),('caravan_hub','caravan_hub_pm.txt','horse')]:
        path=ROOT/'common/production_methods'/filename
        for tier,output in [(1,10),(2,15),(3,20)]:
            key=f'pm_building_{building}_main_{tier}'
            edit(path,lambda t:replace_node(t,key,lambda s:set_jobs(rewrite_quantities(s,{('input',input_good):tier,('output','merchant_marine'):output}),jobs[tier])))
    edit(ROOT/'common/production_methods/port_pm.txt',lambda t:replace_node(t,'pm_building_port_main_0',lambda s:set_jobs(s,{'laborers':40,'clerks':8,'bureaucrats':2})))

def original_pm(path,key,fallback):
    if path not in ORIGINALS:
        result=subprocess.run(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],capture_output=True)
        ORIGINALS[path]={n.key:n for n in a.parse(result.stdout.decode('utf-8-sig'))} if not result.returncode else {}
    return ORIGINALS[path].get(key,fallback)

def rewrite_quantities(text,amounts):
    n=a.parse(text)[0];changes=[]
    existing=set()
    for kind,g,q,scale,v in a.goods(n):
        existing.add((kind,g))
        if (kind,g) in amounts:changes.append((v.start,v.end,f'{v.key} = {amounts[kind,g]}'))
    for start,end,value in sorted(changes,reverse=True):text=text[:start]+value+text[end:]
    missing={k:v for k,v in amounts.items() if k not in existing}
    if missing:
        scale=a.parse(text)[0].child('building_modifiers').child('workforce_scaled')
        text=text[:scale.end-1]+''.join(f'\n\t\t\tgoods_{k}_{g}_add = {v}\n' for (k,g),v in missing.items())+'\t\t'+text[scale.end-1:]
    return text

def rebalance():
    prices={n.key:float(n.scalar('cost')) for n in a.parse((ROOT/'common/goods/uyr_goods.txt').read_text(encoding='utf-8-sig'))}
    pms,paths,_=a.load('production_methods',True)
    groups,gpaths,_=a.load('production_method_groups',True)
    buildings,_,_=a.load('buildings')
    used={g for k,b in buildings.items() if k not in a.EXCLUDED for g in b.words('production_method_groups')}
    primary_groups={b.words('production_method_groups')[0] for b in buildings.values() if b.words('production_method_groups') and a.sector_of(b) in {'agriculture','light_industry','heavy_industry','resource'}}
    for group in primary_groups:
        seq=[k for k in groups[group].words('production_methods') if k in pms and custom(paths[k]) and any(kind=='output' and q>0 for kind,g,q,s,n in a.goods(pms[k]))]
        for index,key in enumerate(seq):
            if 'behaviorism' not in pms[key].words('unlocking_technologies'):continue
            tech=f'production_age_{[1,2,3,5][min(index,3)]}'
            def gate(s):
                n=a.parse(s)[0].child('unlocking_technologies')
                return s[:n.start]+re.sub(r'\bbehaviorism\b',tech,s[n.start:n.end])+s[n.end:]
            edit(paths[key],lambda t:replace_node(t,key,gate))
    pms,paths,_=a.load('production_methods',True)
    targets={}
    ranks={}
    primary_sectors={b.words('production_method_groups')[0]:a.sector_of(b) for b in buildings.values() if b.words('production_method_groups')}
    weights=a.wage_weights()
    for group in sorted(used):
        if group not in groups:continue
        seq=[p for p in groups[group].words('production_methods') if p in pms and custom(paths[p]) and any(k=='output' and q>0 for k,g,q,s,n in a.goods(pms[p]))]
        for index,key in enumerate(seq):
            if '_ivory_' in key and 'camp' not in key:continue # Explicit, matched luxury recipes.
            if key.startswith(('pm_building_port_main_','pm_building_caravan_hub_main_')):continue
            pm=pms[key];emp=max(0,a.workers(pm))
            rank=0 if a.is_alternative(group) else min(index,3)
            if emp>=500:
                scale=emp/3000
                out=[900,1500,2200,3100][rank]*scale
                surplus=[600,950,1350,1850][rank]*scale
            else:
                out=[300,600,900,1200][rank]
                surplus=[150,300,450,600][rank]
            if key.startswith('pm_uyr_transport_'):
                out=[300,600,900,1200][rank];surplus=out*.5
            sector=primary_sectors.get(group)
            if sector in {'agriculture','light_industry','heavy_industry','resource'} and emp>0:
                output_values={
                    'agriculture':[900,1500,2200,3100],
                    'resource':[1000,1700,2500,3500],
                    'light_industry':[1400,2100,3000,4200],
                    'heavy_industry':[1900,2900,4200,5900],
                }
                net_values={
                    'agriculture':[450,750,1150,1650],
                    'resource':[500,850,1250,1800],
                    'light_industry':[800,1200,1750,2450],
                    'heavy_industry':[1200,1800,2600,3600],
                }
                out=output_values[sector][rank]*emp/3000
                surplus=net_values[sector][rank]*emp/3000+max(0,a.wage_units(pm,weights))*5/52
            # Standalone ivory production uses the same value targets as other resources.
            targets[key]=(out,surplus)
            ranks[key]=rank
    for key,(out,surplus) in targets.items():
        path=paths[key];full=path.read_text(encoding='utf-8-sig')
        current=next(n for n in a.parse(full) if n.key==key)
        template=original_pm(path,key,current)
        raw=a.goods(template)
        raw=[(k,{'gem':'gems','liqour':'liquor'}.get(g,g),q,s,n) for k,g,q,s,n in raw]
        ins=[(g,q) for k,g,q,s,n in raw if k=='input' and q>0 and g in prices]
        pos=[(g,q) for k,g,q,s,n in raw if k=='output' and q>0 and g in prices]
        neg=[(g,q) for k,g,q,s,n in a.goods(current) if k=='output' and q<0]
        if not pos:continue
        lost=-sum(q*prices[g] for g,q in neg)
        base_out=sum(q*prices[g] for g,q in pos)
        # Round output first, then balance materials against its actual value.
        rounded={(g):five(q*out/base_out) for g,q in pos}
        rounded_value=sum(q*prices[g] for g,q in rounded.items())
        available=max(0,rounded_value-surplus-lost)
        amounts={}
        # Raw extractors also pay for equipment; no free, high-margin resource outlier.
        if not ins:ins=[('grain' if '_sheep_' in key else 'tools',1)]
        base_in=sum(q*prices[g] for g,q in ins)
        for g,q in ins:amounts['input',g]=max(1,round(q*available/base_in))
        # Integer rounding must not push a recipe beyond its shared material budget.
        while sum(q*prices[g] for (k,g),q in amounts.items() if k=='input')>available:
            choices=[g for (kind,g),q in amounts.items() if kind=='input' and q>1]
            if not choices:break
            g=min(choices,key=lambda g:prices[g])
            amounts['input',g]-=1
        # Keep removals compatible with the weakest base recipe.
        for g,q in neg:amounts['output',g]=-min(abs(round(q)),5)
        actual_in=sum(q*prices[g] for (k,g),q in amounts.items() if k=='input')
        actual_lost=-sum(q*prices[g] for (k,g),q in amounts.items() if k=='output' and q<0)
        for g,q in rounded.items():amounts['output',g]=q
        # Absorb rounding in the input basket as well. Otherwise a five-unit
        # step in an expensive output could create a windfall for one recipe.
        for attempt in range(100):
            budget=sum(q*prices[g] for (k,g),q in amounts.items() if k=='output')-surplus
            for g,q in ins:amounts['input',g]=max(1,round(q*max(0,budget)/base_in))
            actual_in=sum(q*prices[g] for (k,g),q in amounts.items() if k=='input')
            while actual_in>budget:
                choices=[g for (kind,g),q in amounts.items() if kind=='input' and q>1]
                if not choices:break
                g=min(choices,key=lambda g:prices[g])
                amounts['input',g]-=1;actual_in-=prices[g]
            if actual_in<=budget+1e-8:break
            g=min(rounded,key=lambda g:prices[g])
            amounts['output',g]+=5
        else:raise ValueError(f'Cannot quantize {key}')
        # Balanced value targets, integer ingredients and unchanged recipe material mix.
        edit(path,lambda t:replace_node(t,key,lambda s:rewrite_quantities(s,amounts)))
    # Round all custom input baskets, including public services, to integers.
    for path in (ROOT/'common/production_methods').glob('*.txt'):
        if not custom(path) or path.name=='construction_sector_pm.txt':continue
        edit(path,lambda t:re.sub(r'(goods_(?:input|output)_\w+_add\s*=\s*)(-?\d+\.\d+)',lambda m:m[1]+str(round(float(m[2]))),t))
    balance_ports()
    # Optional ivory processing retains matched upgrades with rounded outputs.
    ivory=ROOT/'common/production_methods/uyr_optional_luxury_and_minting.txt'
    for building,product,recipes in [
        ('luxury_furniture_workshop','luxury_furniture',[(1,2,5),(2,4,10)]),
        ('jewelry_workshop','jewelry',[(1,4,5),(2,9,10)]),
    ]:
        for tier,inp,out in recipes:
            edit(ivory,lambda t:replace_node(t,f'pm_building_{building}_ivory_{tier}',lambda s:rewrite_quantities(s,{('input','ivory'):inp,('output',product):out})))
    # Cover every custom output, including disabled legacy recipes.
    for path in (ROOT/'common/production_methods').glob('*.txt'):
        if not custom(path):continue
        edit(path,lambda t:re.sub(r'(goods_output_\w+_add\s*=\s*)(-?\d+(?:\.\d+)?)',lambda m:m[1]+str(five(float(m[2]))),t))
    # Pay the complete building's wage bill and worst secondary recipe costs.
    # Prefer cheaper input baskets to larger output volumes.
    pms,paths,_=a.load('production_methods',True)
    weights=a.wage_weights()
    def net(pm):
        inp,out,_=a.values(pm,prices)
        return out*.85-inp*1.15-a.wage_units(pm,weights)*5/52
    for building in buildings.values():
        bgs=building.words('production_method_groups')
        if not bgs or bgs[0] not in groups:continue
        overhead=0
        for g in bgs[1:]:
            options=[net(pms[k]) for k in groups[g].words('production_methods') if k in pms]
            overhead+=min(options) if options else 0
        for key in groups[bgs[0]].words('production_methods'):
            if key not in targets:continue
            pm=pms[key]
            if not any(k=='output' and q>0 for k,g,q,s,n in a.goods(pm)):continue
            sector=a.sector_of(building)
            rank=ranks[key]
            rate={
                'agriculture':[300,400,650,950],
                'light_industry':[450,650,950,1350],
                'heavy_industry':[650,950,1400,2000],
            }.get(sector,[200,350,550,850])[rank]
            reserve=max(20,rate*a.workers(pm)/3000)
            quantities={(k,g):int(q) for k,g,q,s,n in a.goods(pm)}
            margin=net(pm)+overhead
            while margin<reserve:
                choices=[g for (kind,g),q in quantities.items() if kind=='input' and q>1]
                if choices:
                    g=max(choices,key=lambda g:prices[g]*quantities['input',g])
                    quantities['input',g]-=1;margin+=1.15*prices[g]
                else:
                    g=max((g for (kind,g),q in quantities.items() if kind=='output' and q>0),key=lambda g:prices[g])
                    quantities['output',g]+=5;margin+=.85*prices[g]*5
            edit(paths[key],lambda t:replace_node(t,key,lambda s:rewrite_quantities(s,quantities)))
    # Public service upgrades get declining input cost per principal benefit.
    pms,paths,_=a.load('production_methods',True)
    for group,benefit in a.PUBLIC_BENEFITS.items():
        if group=='pmg_building_construction_sector_main':continue
        if group not in groups:continue
        previous=None
        for key in groups[group].words('production_methods'):
            if key not in pms or not custom(paths[key]):continue
            pm=pms[key];amount=a.benefit_value(pm,benefit)
            if benefit=='state_trade_quantity_mult':amount+=1
            inp=a.values(pm,prices)[0]
            if not amount or not inp:continue
            quantities={('input',g):int(q) for kind,g,q,s,n in a.goods(pm) if kind=='input'}
            if previous:
                while inp/amount>previous*.9:
                    choices=[g for (k,g),q in quantities.items() if q>1]
                    if not choices:break
                    good=max(choices,key=lambda g:quantities['input',g]*prices[g])
                    quantities['input',good]-=1;inp-=prices[good]
                edit(paths[key],lambda t:replace_node(t,key,lambda s:rewrite_quantities(s,quantities)))
            previous=inp/amount
    enforce_progression_and_sectors(buildings,groups,prices,weights)
    print(f'Balanced {len(targets)} custom saleable PMs with integer inputs and outputs; vanilla files excluded.')

def enforce_progression_and_sectors(buildings,groups,prices,weights):
    """Order age-available building recipes, including optional methods."""
    for iteration in range(12):
        changed=False
        pms,paths,_=a.load('production_methods',True)
        for group in groups.values():
            if a.is_alternative(group.key):continue
            seq=[k for k in group.words('production_methods') if k in pms and custom(paths[k]) and all(g in prices for kind,g,q,s,n in a.goods(pms[k])) and any(kind=='output' and q>0 for kind,g,q,s,n in a.goods(pms[k]))]
            previous=None
            for key in seq:
                pm=pms[key];inp,out,gross=a.values(pm,prices)
                pay=a.wage_units(pm,weights)*5/52
                quantities={(kind,g):int(q) for kind,g,q,s,n in a.goods(pm)}
                updated=False
                if previous:
                    while gross<=previous[0] or gross-pay<=previous[1]:
                        g=min((g for (kind,g),q in quantities.items() if kind=='output' and q>0),key=lambda g:prices[g])
                        quantities['output',g]+=5;gross+=5*prices[g];updated=True
                previous=(gross,gross-pay)
                if updated:
                    edit(paths[key],lambda t:replace_node(t,key,lambda s:rewrite_quantities(s,quantities)))
                    changed=True
        for lower,higher in [('agriculture','light_industry'),('light_industry','heavy_industry')]:
            pms,paths,_=a.load('production_methods',True)
            scores=a.sector_combinations(buildings,groups,pms,paths,prices,weights)
            ceilings={}
            for row in scores:
                if row['sector']==lower:ceilings[row['age']]=max(ceilings.get(row['age'],float('-inf')),row['profit_per_3000'])
            deficits={}
            for row in scores:
                if row['sector']!=higher or row['age'] not in ceilings:continue
                target=ceilings[row['age']]+200
                missing=target*row['reference_capacity']/3000-row['profit']
                if missing>1e-6:deficits[row['primary']]=max(deficits.get(row['primary'],0),missing)
            for key,missing in deficits.items():
                pm=pms[key]
                g=min((g for kind,g,q,s,n in a.goods(pm) if kind=='output' and q>0),key=lambda g:prices[g])
                amount=next(q for kind,good,q,s,n in a.goods(pm) if kind=='output' and good==g)
                quantity=int(amount)+5*math.ceil(missing/(5*prices[g])-1e-9)
                edit(paths[key],lambda t:replace_node(t,key,lambda s:rewrite_quantities(s,{('output',g):quantity})))
                changed=True
        if not changed:return
    raise ValueError('Sector/progression balancing did not converge')

if __name__=='__main__':
    if '--apply' not in sys.argv:raise SystemExit('Pass --apply to rebalance custom recipes.')
    rebalance()

"""Read-only joint public-service and bullion stress audit.

--capture-before saves a baseline before applying balance_minting.py.
--write-report writes the checked design, comparisons and sensitivity grids.
Government wages include aristocrats, unlike private-sector wage calculations.
"""
import itertools
import json
import re
import sys

import economy_audit as a
import balance_minting as policy

REPORT = a.ROOT/'docs/economy'
BASELINE = REPORT/'minting_before.json'


def weights(base_only=False):
    result = {}
    for root in ([a.BASE] if base_only else [a.BASE, a.ROOT]):
        for path in (root/'common/pop_types').glob('*.txt'):
            text = path.read_text(encoding='utf-8-sig')
            key = re.search(r'^\s*(\w+)\s*=', text)
            wage = re.search(r'\bwage_weight\s*=\s*([\d.]+)', text)
            if key and wage:
                result[key[1]] = float(wage[1])
    return result


def recipe(nodes, prices, wage_weights, public=False):
    inputs, outputs, jobs = {}, {}, {}
    for node in nodes:
        for kind, good, quantity, scale, _ in a.goods(node):
            target = inputs if kind == 'input' else outputs
            target[good] = target.get(good, 0) + quantity
        bm = node.child('building_modifiers')
        for scale in bm.value if bm else []:
            for n in scale.value if isinstance(scale.value, list) else []:
                match = re.fullmatch(r'building_employment_(\w+)_add', n.key)
                if match:
                    jobs[match[1]] = jobs.get(match[1], 0) + float(n.value)
    assert set(jobs) <= wage_weights.keys(), f'Unknown professions: {jobs.keys()-wage_weights.keys()}'
    cost = sum(prices[g]*q for g, q in inputs.items())
    revenue = sum(prices[g]*q for g, q in outputs.items())
    units = sum(q*wage_weights[p] for p, q in jobs.items())
    return dict(pms=[n.key for n in nodes], inputs=inputs, outputs=outputs,
                jobs=jobs, workers=sum(jobs.values()), weighted_jobs=units,
                goods_cost=cost, revenue=revenue, wages=units*5/52,
                cost=cost+units*5/52, profit=revenue-cost-units*5/52,
                bureaucracy=sum(a.benefit_value(n, 'country_bureaucracy_add') for n in nodes),
                tax_capacity=sum(a.benefit_value(n, 'state_tax_capacity_add') for n in nodes),
                treasury_minting=sum(a.benefit_value(n, 'country_minting_add') for n in nodes))


def snapshot():
    pms, _, _ = a.load('production_methods', True)
    groups, _, _ = a.load('production_method_groups', True)
    prices = {n.key: float(n.scalar('cost')) for n in a.parse((a.ROOT/'common/goods/uyr_goods.txt').read_text(encoding='utf-8-sig'))}
    ww = weights()
    private_weights = a.wage_weights()
    rows = {}
    for main, silver, gold, professionalism, religion in itertools.product(
            range(1, 5), range(3), range(3),
            ['pm_hereditary_bureaucrats', 'pm_professional_bureaucrats'],
            ['pm_religious_bureaucrats', 'pm_secular_bureaucrats']):
        keys = [f'pm_building_chancery_main_{main}', f'pm_building_chancery_silver_{silver}',
                f'pm_building_chancery_gold_{gold}', professionalism, religion]
        row = recipe([pms[k] for k in keys], prices, ww, True)
        row.update(main=main, silver=silver, gold=gold,
                   cost_per_bureaucracy=row['cost']/row['bureaucracy'],
                   cost_per_tax_capacity=row['cost']/row['tax_capacity'])
        rows['/'.join(keys)] = row
    mines = {}
    for metal in ['silver', 'gold']:
        transport = groups[f'pmg_transportation_building_{metal}_mine'].words('production_methods')
        for tier, secondary in itertools.product(range(1, 5), transport):
            key = f'pm_building_{metal}_mine_main_{tier}'
            row = recipe([pms[key], pms[secondary]], prices, private_weights)
            row.update(metal=metal, tier=tier, transport=secondary)
            mines[f'{metal}/{tier}/{secondary}'] = row
    field = recipe([pms['pm_building_gold_field_main_1']], prices, private_weights)
    return dict(prices=prices, public_wage_weights=ww, offices=rows, mines=mines, gold_field=field)


def main():
    current = snapshot()
    if '--capture-before' in sys.argv:
        if BASELINE.exists():
            raise SystemExit('Baseline already exists; refusing to overwrite it.')
        BASELINE.write_text(json.dumps(current, indent=2)+'\n', encoding='utf-8')
        print('Captured unmodified minting baseline.')
        return
    pms, _, _ = a.load('production_methods', True)
    groups, _, _ = a.load('production_method_groups', True)
    techs, _, _ = a.load('technology/technologies', True)
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    check(groups['pmg_building_chancery_main'].scalar('ai_selection') == 'most_productive', 'Main: AI selection')
    all_mine_outputs = {resource: policy.ORDINARY_MINE_OUTPUTS for resource in policy.STARTING_ORDINARY_MINES}
    all_mine_outputs.update(policy.MINE_OUTPUTS)
    for metal, outputs in all_mine_outputs.items():
        for tier, quantity in enumerate(outputs, 1):
            good = 'gems' if metal == 'gem' else metal
            node = pms[f'pm_building_{metal}_mine_main_{tier}']
            check(a.benefit_value(node, f'goods_output_{good}_add') == quantity,
                  f'{metal} {tier}: mine output policy')
            check(a.benefit_value(node, 'goods_input_tools_add') == policy.MINE_TOOLS[tier-1],
                  f'{metal} {tier}: mine equipment progression')
    for key in [f'pm_building_chancery_main_{i}' for i in range(1, 5)] + [
            f'pm_building_chancery_{metal}_{i}' for metal in ['silver', 'gold'] for i in range(3)]:
        texture = pms[key].scalar('texture').strip('"')
        check((a.ROOT/texture).exists() or (a.BASE/texture).exists(), f'{key}: missing texture {texture}')
    for tier, (bur, tax, paper, books, tech) in enumerate(policy.MAIN, 1):
        node = pms[f'pm_building_chancery_main_{tier}']
        check(a.benefit_value(node, 'country_bureaucracy_add') == bur, f'main {tier}: bureaucracy')
        check(a.benefit_value(node, 'state_tax_capacity_add') == tax, f'main {tier}: tax capacity')
        check(a.benefit_value(node, 'goods_input_paper_add') == paper, f'main {tier}: paper')
        check(a.benefit_value(node, 'goods_input_book_add') == books, f'main {tier}: books')
        check(node.words('unlocking_technologies') == ([tech] if tech else []), f'main {tier}: gate')
        if tech:
            check(tech in techs, f'main {tier}: missing tech')
    for metal, recipes in [('silver', policy.SILVER), ('gold', policy.GOLD)]:
        check(groups[f'pmg_building_chancery_{metal}'].scalar('ai_selection') == 'most_productive', f'{metal}: AI selection')
        previous = None
        for tier, (qty, bur, tax, tech) in enumerate(recipes):
            node = pms[f'pm_building_chancery_{metal}_{tier}']
            check(a.benefit_value(node, f'goods_input_{metal}_add') == qty, f'{metal} {tier}: quantity')
            check(a.benefit_value(node, 'country_bureaucracy_add') == bur, f'{metal} {tier}: bureaucracy')
            check(a.benefit_value(node, 'state_tax_capacity_add') == tax, f'{metal} {tier}: tax')
            check(node.words('unlocking_technologies') == ([tech] if tech else []), f'{metal} {tier}: gate')
            if tech:
                check(tech in techs, f'{metal} {tier}: missing tech')
            if qty:
                rates = (qty*current['prices'][metal]/bur, qty*current['prices'][metal]/tax)
                if previous:
                    check(all(x < y for x, y in zip(rates, previous)), f'{metal}: upgrade benefit efficiency')
                previous = rates
    base_mod = (a.ROOT/'common/static_modifiers/aoc_country_modifiers.txt').read_text(encoding='utf-8-sig')
    check('state_tax_capacity_add' not in base_mod, 'Vanilla base tax capacity is still overridden')

    # Compare complete offices, including mandatory staffing groups, against
    # vanilla. In age one use vanilla's available paper PM, not its primitive PM.
    vanilla = {n.key: n for n in a.parse((a.BASE/'common/production_methods/07_government.txt').read_text(encoding='utf-8-sig'))}
    vanilla_goods = {n.key: float(n.scalar('cost')) for n in a.parse((a.BASE/'common/goods/00_goods.txt').read_text(encoding='utf-8-sig'))}
    checkpoints = [(1, 1, 1, 'pm_horizontal_drawer_cabinets'),
                   (2, 2, 1, 'pm_horizontal_drawer_cabinets'),
                   (3, 2, 1, 'pm_vertical_filing_cabinets'),
                   (4, 2, 2, 'pm_switch_boards')]
    comparisons = []
    for main_tier, silver, gold, reference in checkpoints:
        keys = [f'pm_building_chancery_main_{main_tier}', f'pm_building_chancery_silver_{silver}',
                f'pm_building_chancery_gold_{gold}', 'pm_hereditary_bureaucrats', 'pm_religious_bureaucrats']
        mod = current['offices']['/'.join(keys)]
        van = recipe([vanilla[k] for k in [reference, 'pm_hereditary_bureaucrats', 'pm_religious_bureaucrats']], vanilla_goods, weights(True), True)
        ratio = (mod['cost']/mod['bureaucracy'])/(van['cost']/van['bureaucracy'])
        check(.85 <= ratio <= 1.15, f'main {main_tier}: bureaucracy unit cost outside vanilla +/-15%')
        check(mod['tax_capacity'] <= van['tax_capacity']*1.3, f'main {main_tier}: excessive tax capacity')
        comparisons.append(dict(main=main_tier, mod=mod, vanilla=van, bureaucracy_unit_cost_ratio=ratio))
    check(comparisons[-1]['mod']['tax_capacity'] == 30, 'Final bimetallic office must match vanilla 30 tax capacity')

    stress_rows = []
    for key, row in list(current['mines'].items()) + [('gold_field', current['gold_field'])]:
        stress = row['revenue']*.5-row['goods_cost']*1.25-row['wages']
        check(stress > 0, f'{key}: loses money at metal -50%, inputs +25%, annual base wage 5')
        row['stressed_profit'] = stress
        row['break_even_metal_price_factor'] = (row['goods_cost']*1.25+row['wages'])/row['revenue']
        for metal_factor, input_factor, wage in itertools.product([.25, .5, .75, 1, 1.25, 1.9], [1, 1.25], [2.5, 5, 10]):
            stress_rows.append(dict(recipe=key, metal_price_factor=metal_factor, input_price_factor=input_factor,
                                    annual_base_wage=wage, private_profit=row['revenue']*metal_factor-row['goods_cost']*input_factor-row['weighted_jobs']*wage/52))
    for metal in ['silver', 'gold']:
        for secondary in ['pm_road_carts', f'pm_uyr_transport_{metal}_1']:
            series = [current['mines'][f'{metal}/{tier}/{secondary}'] for tier in range(1, 5)]
            check(all(right['profit'] > left['profit'] for left, right in zip(series, series[1:])), f'{metal}/{secondary}: upgrade private profit regression')
    # Check complete ordinary/precious mines, including every attached secondary
    # recipe. Upgrades must improve both base and adverse-price private profit.
    buildings, _, _ = a.load('buildings')
    mine_upgrade_rows = []
    private_weights = a.wage_weights()
    for resource in all_mine_outputs:
        building = buildings[f'building_{resource}_mine']
        secondary_groups = building.words('production_method_groups')[1:]
        choices = [groups[g].words('production_methods') for g in secondary_groups]
        for secondary in itertools.product(*choices):
            previous = None
            for tier in range(1, 5):
                keys = [f'pm_building_{resource}_mine_main_{tier}', *secondary]
                if any(not set(pms[k].words('unlocking_production_methods')).issubset(keys) for k in keys):
                    continue
                row = recipe([pms[k] for k in keys], current['prices'], private_weights)
                stressed = row['revenue']*.85-row['goods_cost']*1.15-row['wages']
                check(row['profit'] > 0 and stressed > 0, f'{resource}/{tier}/{secondary}: hiring margin')
                if previous:
                    check(row['profit'] > previous[0] and stressed > previous[1],
                          f'{resource}/{tier}/{secondary}: base or stressed upgrade regression')
                previous = (row['profit'], stressed)
                mine_upgrade_rows.append(dict(resource=resource, tier=tier, secondary=' '.join(secondary),
                                              output=all_mine_outputs[resource][tier-1], tools=policy.MINE_TOOLS[tier-1],
                                              goods_cost=row['goods_cost'], revenue=row['revenue'], wages=row['wages'],
                                              private_profit=row['profit'], stressed_profit=stressed))
    silver_minting = [a.benefit_value(pms[f'pm_building_silver_mine_main_{tier}'], 'country_minting_add') for tier in range(1, 5)]
    check(silver_minting == [300, 600, 1200, 2400], 'Silver mine treasury progression')
    summary = dict(office_configurations=len(current['offices']), mine_configurations=len(current['mines']),
                   sensitivity_scenarios=len(stress_rows), mine_upgrade_configurations=len(mine_upgrade_rows), errors=errors,
                   assumptions='Base prices; full staffing; annual reference base wage 5; public aristocrats paid; treasury minting excluded from mine private profit. No live AI simulation.')
    if '--write-report' in sys.argv:
        current.update(summary=summary, comparisons=comparisons)
        (REPORT/'minting_balance.json').write_text(json.dumps(current, indent=2)+'\n', encoding='utf-8')
        a.csvfile(REPORT/'minting_mine_sensitivity.csv', stress_rows)
        a.csvfile(REPORT/'mine_upgrade_progression.csv', mine_upgrade_rows)
        write_report(current)
    print(json.dumps(summary, indent=2))
    if errors:
        raise SystemExit(1)


def write_report(data):
    before = json.loads(BASELINE.read_text(encoding='utf-8')) if BASELINE.exists() else None
    lines = ['# Coinage, administration and precious-metal balance', '',
             'Implemented 6 November 2026. This supersedes the earlier proposal in vanilla_public_cost_comparison.md; that file and its JSON are a pre-change historical comparison.', '',
             '## Design', '',
             'Vanilla-sized tax capacity and similar public cost per bureaucracy, with paper and bullion sharing the output. The no-metal office remains functional; imported or domestic bullion enables the efficient path. Both minting groups grant bureaucracy AND tax capacity. Gold is available through the era-one minting_house technology; advanced silver accompanies era-two paper; advanced gold requires production age four. Paper upgrades use formalized_administration (2), printing_press (3), administrative_suzerainty (4).', '',
             'Base state tax capacity is restored to vanilla 100 by removing the mod -80 injection. Other global modifiers and construction recipes are unchanged. Existing PM IDs and staffing remain; existing saves retain their chosen PM IDs. A previously selected advanced method can now require research that the country lacks; recheck those offices after loading.', '',
             '| Main office | Bureaucracy | Tax capacity | Paper/week | Books/week |', '|---|---:|---:|---:|---:|']
    for i, (bur, tax, paper, books, gate) in enumerate(policy.MAIN, 1):
        lines.append(f'| {i} | {bur} | {tax} | {paper} | {books} |')
    lines += ['', '| Coinage group | Metal/week | Bureaucracy | Tax capacity |', '|---|---:|---:|---:|']
    for metal, rows in [('Silver', policy.SILVER), ('Gold', policy.GOLD)]:
        for i, (qty, bur, tax, gate) in enumerate(rows):
            lines.append(f'| {metal} {i} | {qty} | {bur} | {tax} |')
    lines += ['', 'All outputs stack across the main, silver and gold groups. Off methods contribute zero. Maximum office output is 110 bureaucracy and 30 capacity, compared with vanilla 100 and 30. This replaces the old potential 155 bureaucracy and 110 capacity. Main output is deliberately lower than before because minting now supplies part of the normal administrative output, rather than a large extra tax-capacity bonus.', '',
              '## Complete office comparisons', '',
              'Full employment, base goods prices, annual reference base wage 5; hereditary/religious staffing includes all 1,500 employees, with £456.73 weekly wages. Public aristocrats receive wages: paid_private_wage=no only excludes wages in private buildings. No scale, law, shortage, government-wage-setting or local-price modifiers.', '',
              '| Stage | Mod bureaucracy / tax | Mod weekly cost | Vanilla bureaucracy / tax | Vanilla weekly cost | Mod cost per bureaucracy vs vanilla |', '|---|---:|---:|---:|---:|---:|']
    for row in data['comparisons']:
        m, v = row['mod'], row['vanilla']
        lines.append(f"| {row['main']} | {m['bureaucracy']:g} / {m['tax_capacity']:g} | £{m['cost']:,.1f} | {v['bureaucracy']:g} / {v['tax_capacity']:g} | £{v['cost']:,.1f} | {(row['bureaucracy_unit_cost_ratio']-1)*100:+.1f}% |")
    lines += ['', 'These use both available metals, not a claim every country can source both. Silver-only starting administration supplies 35 bureaucracy / 4 capacity at £636.73, versus its former 30 / 20 at the same cost. No-metal outputs are the main office table above. All four available profession/religion staffing combinations are represented in the JSON configuration data; all calculations exclude throughput.', '',
              '## AI', '',
              'Both silver and gold groups explicitly use the documented most_productive selection mode; gold previously defaulted to most_profitable. Each active coinage method carries both services, each upgrade improves service per bullion cost, and both off methods remain valid. No fixed high AI weight or event forces countries to buy metals. These definitions expose the intended benefits to the engine; import decisions, affordability and actual AI adoption require an in-game campaign check. The authoring tool does not claim to simulate the engine AI.', '',
              '## Precious-metal mines', '',
              'Main mine output follows a common upgrade pattern: ordinary mines 25/45/65/90, silver and gold 20/35/50/70 (the same approximate multipliers, rounded to fives). Main tool consumption is 3/8/14/22 for all nine mines. Existing staffing, research gates, secondary methods and base goods prices remain. Existing treasury bonuses remain separate; the missing third silver bonus is repaired to 1,200. Mine profit below EXCLUDES treasury minting: money paid to the country is not factory wage revenue.', '',
              '| Mine | Tier | Output before → after | Private profit before → after | Stress profit after |', '|---|---:|---:|---:|---:|']
    for metal in ['silver', 'gold']:
        for tier in range(1, 5):
            key = f'{metal}/{tier}/pm_road_carts'
            row = data['mines'][key]
            old = before['mines'][key] if before else row
            lines.append(f"| {metal} | {tier} | {old['outputs'][metal]:g} → {row['outputs'][metal]:g} | £{old['profit']:,.0f} → £{row['profit']:,.0f} | £{row['stressed_profit']:,.0f} |")
    lines += ['', 'Stress means metal sale prices -50%, input prices +25%, annual base wage 5. Every main + transport combination and gold fields remains profitable in that scenario, and every mine upgrade increases base-price private profit. The wider CSV deliberately includes losing scenarios at still worse prices/higher wages: this is not guaranteed profit at the full ±90% market range.', '',
              'Starting output remains 25 for ordinary mines (coal, stone, iron, copper, tin, lead and gems) and 20 for silver and gold. Coal/stone previously produced 35 because an older policy targeted similar sale values across resources; the new policy preserves consistent quantities instead. Cheaper resources have lower profits. Complete recipes improve both base-price and adverse-price private profit at every main upgrade; see mine_upgrade_progression.csv for every attached secondary configuration. The ordinary-mine adverse scenario uses outputs -15%, inputs +15%, reference annual base wage 5.', '',
              'Gold fields output increases 5 → 10, retaining 1,000 jobs and their existing 250 treasury minting; these smaller, non-buildable fields are separate from mines. A tier-one silver mine produces 20 silver: enough for 6.7 basic-silver offices. A tier-one gold mine produces 20 gold: enough for 10 basic-gold offices. At the final tier, mines supply 14 advanced-silver offices or 23.3 advanced-gold offices. Other industrial bullion demand competes for that supply. Demand, prices and trade still determine realized income; larger supply alone cannot guarantee a price floor. The larger advanced-gold output warrants observing late-game demand and prices in a campaign.', '',
              '## Verification and maintenance', '',
              f"Checked {data['summary']['office_configurations']} office configurations, {data['summary']['mine_configurations']} precious-mine/transport configurations plus gold fields, {data['summary']['sensitivity_scenarios']} mine price/wage scenarios, and {data['summary']['mine_upgrade_configurations']} complete mine-upgrade configurations across nine resources. Vanilla unit-cost comparisons, bullion efficiency, technology gates, defined professions and both service outputs are checked by tools/audit_minting.py. The general economy audit separately checks the mod's recipes and sector ordering.", '',
              'Run `python tools/audit_minting.py --write-report` and `python tools/economy_audit.py`. Reapply the policy with `python tools/balance_minting.py --apply`; the general rebalance calls the same policy last so that it cannot silently undo these targets.', '',
              'Remaining verification: launch with the mod, check tax-capacity tooltips, inspect the AI\'s coinage selections/imports and mine hiring in a campaign. No game launch or campaign simulation was performed here. Existing unrelated vanilla-dependency warnings remain outside this change.', '']
    (REPORT/'minting_balance.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()

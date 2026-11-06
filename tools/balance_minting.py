"""Author public administration, bullion and shared main-mine progression.

Run with --apply. Imported by rebalance_economy so that a general economy
rebalance cannot silently undo the public-service and precious-metal targets.
"""
import re
import economy_audit as a

MAIN = [
    # bureaucracy, tax capacity, paper, technology
    (20, 2, 0, None),
    (35, 6, 8, 'formalized_administration'),
    (45, 10, 10, 'printing_press'),
    (55, 20, 12, 'administrative_suzerainty'),
]
SILVER = [(0, 0, 0, None), (3, 15, 2, None),
          (5, 30, 4, 'formalized_administration')]
GOLD = [(0, 0, 0, None), (2, 15, 3, 'minting_house'),
        (3, 25, 6, 'production_age_4')]
MINE_OUTPUTS = {'silver': [20, 35, 50, 70], 'gold': [20, 35, 50, 70]}
STARTING_ORDINARY_MINES = ['coal', 'stone', 'iron', 'copper', 'tin', 'lead', 'gem']
ORDINARY_MINE_OUTPUTS = [25, 45, 65, 90]
MINE_TOOLS = [3, 8, 14, 22]


def write(path, text):
    raw = path.read_bytes() if path.exists() else b''
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') or path.suffix == '.yml' else b''
    newline = '\r\n' if b'\r\n' in raw else '\n'
    text = '\n'.join(line.rstrip() for line in text.splitlines()).rstrip() + '\n'
    data = bom + text.replace('\n', newline).encode('utf-8')
    if raw != data:
        path.write_bytes(data)


def replace_node(text, key, replacement):
    node = next(n for n in a.parse(text) if n.key == key)
    return text[:node.start] + replacement + text[node.end:]


def mint_node(metal, tier, recipe):
    quantity, bureaucracy, tax, technology = recipe
    color = 'silver' if metal == 'silver' else 'yellow'
    texture = f'base{tier}_{color}' if tier else f'no_{metal}_minting'
    unlock = f'\n\tunlocking_technologies = {{ {technology} }}\n' if technology else ''
    inputs = (f'\n\tbuilding_modifiers = {{\n\t\tworkforce_scaled = {{\n'
              f'\t\t\tgoods_input_{metal}_add = {quantity}\n\t\t}}\n\t}}\n') if quantity else ''
    return f'''pm_building_chancery_{metal}_{tier} = {{
\ttexture = "gfx/interface/icons/production_method_icons/{texture}.dds"
{unlock}
\tcountry_modifiers = {{
\t\tworkforce_scaled = {{ country_bureaucracy_add = {bureaucracy} }}
\t}}
\tstate_modifiers = {{
\t\tworkforce_scaled = {{ state_tax_capacity_add = {tax} }}
\t}}
{inputs}}}'''


def apply():
    root = a.ROOT
    snippets = ['# Paper organization and coinage share the vanilla-scale public outputs.\n'
                '# Minting groups are additive; off options provide no benefits.']
    icons = ['simple_organization', 'horizontal_drawer_cabinets',
             'vertical_filing_cabinets', 'telephone_switchboards']
    for tier, (bureaucracy, tax, paper, technology) in enumerate(MAIN, 1):
        unlock = f'\n\tunlocking_technologies = {{ {technology} }}\n' if technology else ''
        inputs = f'\n\t\tworkforce_scaled = {{ goods_input_paper_add = {paper} }}' if paper else ''
        snippets.append(f'''pm_building_chancery_main_{tier} = {{
\ttexture = "gfx/interface/icons/production_method_icons/{icons[tier-1]}.dds"
{unlock}
\tcountry_modifiers = {{
\t\tworkforce_scaled = {{ country_bureaucracy_add = {bureaucracy} }}
\t}}
\tstate_modifiers = {{
\t\tworkforce_scaled = {{ state_tax_capacity_add = {tax} }}
\t}}
\tbuilding_modifiers = {{{inputs}
\t\tlevel_scaled = {{ building_employment_clerks_add = 500 }}
\t}}
}}''')
    snippets.extend(mint_node('silver', tier, recipe) for tier, recipe in enumerate(SILVER))
    write(root/'common/production_methods/chancery_pm.txt', '\n\n'.join(snippets))
    path = root/'common/production_methods/uyr_optional_luxury_and_minting.txt'
    text = path.read_text(encoding='utf-8-sig')
    for tier, recipe in enumerate(GOLD):
        text = replace_node(text, f'pm_building_chancery_gold_{tier}', mint_node('gold', tier, recipe))
    write(path, text)

    path = root/'common/production_method_groups/uyr_government.txt'
    text = path.read_text(encoding='utf-8-sig')
    for key in ['pmg_building_chancery_main', 'pmg_building_chancery_silver', 'pmg_building_chancery_gold']:
        node = next(n for n in a.parse(text) if n.key == key)
        block = text[node.start:node.end]
        if node.child('ai_selection'):
            block = re.sub(r'(ai_selection\s*=\s*)\w+', r'\g<1>most_productive', block)
        else:
            block = block.replace('{', '{\n\tai_selection = most_productive', 1)
        text = replace_node(text, key, block)
    write(path, text)

    # Restore vanilla's per-state free tax capacity (100), leaving other
    # intentional Age of Crowns global modifiers alone.
    path = root/'common/static_modifiers/aoc_country_modifiers.txt'
    text = path.read_text(encoding='utf-8-sig')
    text = re.sub(r'^\s*state_tax_capacity_add\s*=\s*-80\s*\n', '', text, flags=re.M)
    write(path, text)

    for metal, outputs in MINE_OUTPUTS.items():
        path = root/f'common/production_methods/{metal}mine_pm.txt'
        text = path.read_text(encoding='utf-8-sig')
        for tier, output in enumerate(outputs, 1):
            key = f'pm_building_{metal}_mine_main_{tier}'
            node = next(n for n in a.parse(text) if n.key == key)
            block = text[node.start:node.end]
            block = re.sub(rf'(goods_output_{metal}_add\s*=\s*)\d+', rf'\g<1>{output}', block)
            block = re.sub(r'(goods_input_tools_add\s*=\s*)\d+', rf'\g<1>{MINE_TOOLS[tier-1]}', block)
            if metal == 'silver' and tier == 3:
                # Existing 300 / 600 / [missing] / 2400 treasury progression.
                if not node.child('country_modifiers'):
                    block = block[:-1] + '''\tcountry_modifiers = {
\t\tworkforce_scaled = { country_minting_add = 1200 }
\t}
}'''
            text = replace_node(text, key, block)
        write(path, text)
    # All main extraction tiers use a consistent physical-quantity progression.
    # Do not inflate cheap coal/stone output to match an expensive ore's revenue.
    for resource in STARTING_ORDINARY_MINES:
        path = root/f'common/production_methods/{resource}mine_pm.txt'
        text = path.read_text(encoding='utf-8-sig')
        for tier, output in enumerate(ORDINARY_MINE_OUTPUTS, 1):
            key = f'pm_building_{resource}_mine_main_{tier}'
            node = next(n for n in a.parse(text) if n.key == key)
            block = re.sub(r'(goods_output_\w+_add\s*=\s*)\d+', rf'\g<1>{output}', text[node.start:node.end])
            block = re.sub(r'(goods_input_tools_add\s*=\s*)\d+', rf'\g<1>{MINE_TOOLS[tier-1]}', block)
            text = replace_node(text, key, block)
        write(path, text)
    path = root/'common/production_methods/gold_field_pm.txt'
    write(path, re.sub(r'(goods_output_gold_add\s*=\s*)\d+', r'\g<1>10', path.read_text(encoding='utf-8-sig')))


if __name__ == '__main__':
    import sys
    if '--apply' not in sys.argv:
        raise SystemExit('Pass --apply to author the minting balance.')
    apply()
    print('Applied administration, minting, AI-selection and mine progression policy.')

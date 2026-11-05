"""Static integration audit; run with Python 3, optionally passing the game path."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    'C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game')
FILES = [
    'common/laws/01_colonial_nation.txt',
    'common/scripted_triggers/aoc_colonial_nation_triggers.txt',
    'common/scripted_effects/aoc_colonial_nation_effects.txt',
    'common/static_modifiers/aoc_colonial_nation_modifiers.txt',
    'common/on_actions/aoc_colonial_nation_on_actions.txt',
    'common/scripted_buttons/00_colonial_administration_buttons.txt',
    'common/scripted_buttons/england_canada_colonization_buttons.txt',
    'common/scripted_buttons/england_overseas_buttons.txt',
    'common/ai_strategies/00_default_strategy.txt',
    'common/defines/aoc_ai.txt',
    'common/state_traits/colony_traits.txt',
]


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8-sig')


def parse(text):
    tokens = re.findall(r'#[^\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>!?"#]+', text)
    tokens = [t for t in tokens if not t.startswith('#')]
    pos = 0

    def block(nested=False):
        nonlocal pos
        result = []
        while pos < len(tokens) and tokens[pos] != '}':
            key = tokens[pos]
            pos += 1
            assert key not in '{}', key
            value = None
            if pos < len(tokens) and tokens[pos] in ('=', '?=', '>=', '<=', '!=', '>', '<'):
                pos += 1
                assert pos < len(tokens), key
                if tokens[pos] == '{':
                    pos += 1
                    value = block(True)
                else:
                    assert tokens[pos] != '}', key
                    value = tokens[pos]
                    pos += 1
            result.append((key, value))
        if nested:
            assert pos < len(tokens) and tokens[pos] == '}', 'Unclosed block'
            pos += 1
        return result

    result = block()
    assert pos == len(tokens), 'Unexpected closing brace'
    return result


def walk(nodes):
    for key, value in nodes:
        yield key, value
        if isinstance(value, list):
            yield from walk(value)


trees = {f: parse(read(f)) for f in FILES}
law = dict(trees[FILES[0]])['law_colonial_nation']
assert dict(law)['group'] == 'lawgroup_major_government_reform'
assert dict(dict(law)['modifier'])['state_working_adult_ratio_add'] == '0.10'
for restriction in ('is_visible', 'can_enact', 'can_impose'):
    assert dict(law)[restriction] == [('aoc_is_or_was_colonial_nation', 'yes')]
eligibility = dict(dict(trees[FILES[1]])['aoc_is_or_was_colonial_nation'])['OR']
assert ('is_country_type', 'colonial') in eligibility
assert ('has_variable', 'aoc_was_colonial_nation') in eligibility

effect = dict(trees[FILES[2]])['aoc_initialize_colonial_nation_effect']
# Both the law and the timer must sit inside the initialization guard.
guard = dict(dict(effect)['if'])
assert guard['limit'] == [('NOT', [('has_variable', 'aoc_colonial_nation_initialized')])]
assert guard['activate_law'] == 'law_type:law_colonial_nation'
assert dict(guard['add_modifier'])['years'] == '15'
assert ('set_variable', 'aoc_was_colonial_nation') in dict(effect)['if']

hook = ('aoc_initialize_colonial_nation_effect', 'yes')
for relative, expected in zip(FILES[5:8], (14, 5, 3)):
    tree = trees[relative]
    created = [v for k, v in walk(tree) if k == 'on_created']
    hooked = [v for v in created if hook in v]
    assert len(hooked) == expected, (relative, len(hooked))
    for v in created:
        is_company = ('set_country_type', 'company') in v
        assert (hook in v) != is_company, 'Missing nation hook or unwanted company hook'

modifier_docs = read('docs/modifiers.log')
for key, value in dict(trees[FILES[3]])['aoc_colonial_settlement_protection']:
    if key != 'icon':
        assert f'{key}:' in modifier_docs, f'Unsupported modifier: {key}'
native_defines = (GAME / 'common/defines/00_ai.txt').read_text(encoding='utf-8-sig')
for key, value in dict(trees[FILES[9]])['NAI']:
    assert re.search(r'\b' + re.escape(key) + r'\s*=', native_defines), key
for relative in FILES[:4]:
    for key, value in walk(trees[relative]):
        if key == 'icon':
            icon = value.strip('"')
            assert (ROOT / icon).exists() or (GAME / icon).exists(), icon
loc = (ROOT / 'localization/english/aoc_colonial_nation_l_english.yml').read_bytes()
assert loc.startswith(b'\xef\xbb\xbf')
for key in ('law_colonial_nation', 'law_colonial_nation_desc',
            'aoc_colonial_settlement_protection'):
    assert re.search(r'^ ' + key + ':', loc.decode('utf-8-sig'), re.M), key
print(f'PASS: {len(FILES)} scripts parsed; 22 formation paths; law gates, one-time 15-year timer,')
print('      modifier/define references, icons, and localization verified.')

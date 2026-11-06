# Government and construction: Age of Crowns versus installed vanilla

Read-only balance comparison, 6 November 2026. No gameplay files changed. Vanilla source: C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game. The mod targets 1.15.*. This compares installed source definitions, not a running save or an AI campaign. Matching recipe tiers are not matching dates or technologies.

## Method

Each side uses its own goods definitions and actual production recipes. Costs are weekly at base goods prices, full employment, no throughput/shortages, and neutral government wages. Illustrative wages use an annual base wage of £5: sum(jobs × profession wage weight) × 5 / 52. Actual wage levels and budget allocation differ by save. Administration includes all three mandatory PM groups: main method, hereditary bureaucrats, and religious bureaucrats. The mod additionally selects no silver and no gold unless stated. These are valid comparison configurations, not claims about every country's starting laws. No private sale revenue is assigned to bureaucracy or tax capacity.

## Input prices

| Good | Vanilla | Mod |
|---|---:|---:|
| wood | 20 | 20 |
| fabric | 20 | 20 |
| iron | 40 | 40 |
| steel | 50 | 50 |
| tools | 40 | 40 |
| glass | 40 | 40 |
| paper | 30 | 30 |
| gold | 100 | 100 |
| stone | Not defined | 30 |
| cutstone | Not defined | 60 |
| silver | Not defined | 60 |
| book | Not defined | 30 |
| bronze | Not defined | 50 |
| explosives | 50 | 50 |
| electricity | 30 | 30 |

Shared public-input base prices are unchanged. Stone (£30), cut stone (£60), silver (£60), books (£30), and bronze (£50) change the recipe mix. Goods existing in the mod's files are not necessarily used by reachable mod buildings.

## Construction

| Tier / construction per week | Vanilla goods | Mod goods | Vanilla wages | Mod wages | Vanilla total / point | Mod total / point | Mod goods difference |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 / 2 | 2,000 | 1,500 | 129.8 | 101 | 1,064.9 | 800.5 | -25% |
| 2 / 5 | 3,600 | 2,900 | 132.2 | 117.8 | 746.4 | 603.6 | -19.4% |
| 3 / 10 | 5,400 | 5,000 | 137 | 137 | 553.7 | 513.7 | -7.4% |
| 4 / 15 | 7,900 | 6,710 | 146.6 | 146.6 | 536.4 | 457.1 | -15.1% |

Exact recipes (quantity × base price):

- vanilla, tier 1: 25 fabric × 20 + 75 wood × 20 = £2,000.
- mod, tier 1: 25 fabric × 20 + 50 wood × 20 = £1,500.
- vanilla, tier 2: 40 wood × 20 + 20 fabric × 20 + 50 iron × 40 + 10 tools × 40 = £3,600.
- mod, tier 2: 30 wood × 20 + 20 fabric × 20 + 50 stone × 30 + 10 tools × 40 = £2,900.
- vanilla, tier 3: 50 steel × 50 + 40 glass × 40 + 10 explosives × 50 + 20 tools × 40 = £5,400.
- mod, tier 3: 25 wood × 20 + 15 fabric × 20 + 50 stone × 30 + 25 cutstone × 60 + 20 tools × 40 + 10 glass × 40 = £5,000.
- vanilla, tier 4: 50 steel × 50 + 40 glass × 40 + 20 explosives × 50 + 30 tools × 40 + 40 electricity × 30 + 10 copper × 40 = £7,900.
- mod, tier 4: 9 wood × 20 + 9 steel × 50 + 68 cutstone × 60 + 27 tools × 40 + 23 glass × 40 = £6,710.

All construction tiers employ 1,000 workers. Mod tier one removes 100 bureaucrats and adds 100 laborers relative to vanilla; tier two replaces 50 bureaucrats with laborers. Other profession mixes match. Construction sectors cost 25 construction points to build on both sides. Existing representative costs also match: administration 100, university 400, wheat farm 200, iron mine 400, textile/tools/paper mills 600. At the same wage scenario, a 600-point building consumes about £480,288 through mod tier-one construction versus £638,942 through vanilla tier one, excluding free construction and other modifiers.

Progression matters: vanilla tier two is era 1, mod tier two era 2; vanilla tier three era 3, mod tier three era 4; both fourth tiers era 5. Therefore vanilla tier two costs £746.4 per point while a mod country still using tier one pays £800.5: the mod can feel about 7% more expensive at this comparison point despite cheaper matched recipes. At the corresponding tier-three transition, mod tier two is £603.6 versus vanilla tier three £553.7, about 9% more. These are illustrations by technology era, not campaign simulations.

A secondary discrepancy: mod tier four grants +0.1% local construction efficiency per sector versus +0.7% at mod tier three and +1% at vanilla tier four. This can weaken an upgrade locally; actual effect depends on sector concentration and other bonuses.

## Bureaucracy and tax collection

| Main tier, no metals | Vanilla weekly cost | Mod weekly cost | Vanilla bureaucracy | Mod bureaucracy | Vanilla tax capacity | Mod tax capacity |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 456.7 | 456.7 | 10 | 20 | 2 | 4 |
| 2 | 756.7 | 756.7 | 50 | 50 | 10 | 4 |
| 3 | 1,056.7 | 786.7 | 65 | 65 | 15 | 4 |
| 4 | 1,406.7 | 906.7 | 100 | 100 | 30 | 4 |

All these administrations employ 1,500 workers, not just the 500 clerks in the main method. With hereditary/religious methods the staff is 500 clerks, 250 aristocrats, 500 bureaucrats and 250 clergy. Their reference weekly wage bill is £456.7 on both sides. Professional/secular staffing gives a different bill but the profession weights themselves are unchanged.

Cost per bureaucracy point at tiers 1–4 is vanilla £45.7 / £15.1 / £16.3 / £14.1, mod £22.8 / £15.1 / £12.1 / £9.1. Therefore there is no general higher cost of producing bureaucracy at matched tiers. The major issue is how early useful upgrades become available and how much extra state expenditure is required alongside them. Mod tier two is era 2; tiers three AND four both require era-six behaviorism. Vanilla corresponding main upgrades are eras 1, 2 and 4.

Tax capacity is separate from national bureaucracy. The mod injects -80 state tax capacity into vanilla base_values (+100), implying 20 base capacity per state before other modifiers. Its no-silver method gives 4 tax capacity at every main tier; the main methods themselves give none. Vanilla main upgrades raise tax capacity 2 → 10 → 15 → 30. With the unchanged 10,000 people per capacity define, unmodified free tax coverage falls from 1,000,000 to 200,000 people per state. These derived totals assume the engine applies the additive INJECT modifiers as authored; they have not been verified in a live tooltip.

Illustration: a state of 1,000,000 taxable people requires 100 capacity. Vanilla base capacity covers that without offices. Mod base capacity leaves an 80-point shortfall: 20 level-one chanceries at 4 each would cost £9,134.6/week and use 30,000 public jobs, before scale/law/tech effects. But two level-one chanceries on the advanced silver option provide 80 capacity for £1,513.5/week and 3,000 jobs. This is a tax-coverage comparison only; it does not imply all offices are fiscally worthwhile or include other reasons to maintain administration.

| Optional chancery method | Additional weekly goods cost | Additional bureaucracy | Tax capacity from this group |
|---|---:|---:|---:|
| silver_1 | 180 | 10 | 20 |
| silver_2 | 300 | 20 | 40 |
| gold_1 | 200 | 15 | 30 |
| gold_2 | 400 | 35 | 70 |

Silver options replace the no-silver group's 4 capacity, rather than adding to it. Gold is a separate group and stacks with the selected silver option. Neither group adds employees. Silver methods have no technology gate in their own definitions; gold requires production ages 2 and 4. These methods buy more than bureaucracy: for example main tier two + advanced silver costs £1,056.7 for 70 bureaucracy and 40 capacity, versus vanilla tier two £756.7 for 50 bureaucracy and 10 capacity. That is a higher office bill, but much cheaper tax capacity per point. Advanced metals are therefore a useful alternative to spamming offices.

The underlying state bureaucracy defines are unchanged: base 10 per incorporated state, population coefficient 4 per 100,000, and minimum institution investment cost 10. The mod adds several extra law-group modifiers to population bureaucracy costs (administrative system, offices, levy law, etc.); exact demand depends on the country's laws and institution levels. Do not treat a government-wage bill, national bureaucracy balance and tax-capacity shortage as the same mechanic.

## Other spending and market conditions

- A royal court consumes 15 paper + 5 books + 5 luxury clothes + 5 luxury furniture: £1,200 goods plus £360.6 reference wages per level. It produces crown attraction rather than bureaucracy/tax capacity. It is not buildable/expandable normally; this is a bill only where a court is actually present.
- A basic bailiff consumes £300 weapons per level. Its silver tax option adds £600 goods and £120.2 wages for 25 capacity; gold adds £500 and £120.2 wages for 35. The base bailiff still refers to the undefined profession servicemen in this installation (which instead defines soldiers). Its exact base wage/hiring behavior needs an in-game check; the report does not invent a wage for it.
- Mod universities are more expensive per building, but more productive: tier-one goods £250 versus £150, innovation 2 versus 1. With religious academia, wage totals are £228.4 each, making cost per innovation about £239.2 versus £378.4. Higher university spending does not by itself mean poor cost efficiency.
- Base market-access price impact is reduced from 0.75 by 0.25, implying 0.50 before laws/technology/roads. Local shortages matter more: a cheap national market does not guarantee cheap construction in the chosen state. The mod allows ±90% goods prices versus vanilla ±75%. At the upper bound, tier-one mod material cost is £2,850 rather than its £1,500 benchmark. Price caps alone do not establish what prices a save reaches.
- troubled_empire adds +50% construction goods cost; it is assigned in China and Jianzhou histories. At base prices, mod wooden materials then cost £2,250 instead of £1,500, exceeding ordinary vanilla £2,000. This modifier is not global.
- strong_nation adds 10 construction for 25 years in several major-country histories, including England. Its expiry can reduce construction capacity without cutting paid sector expenses. GDP-based construction remains another factor.
- All countries receive the mod's land-based taxation in history. Medium settings differ from vanilla: mod land tax 0.55 plus per-capita 0.55 versus vanilla land tax 0.70 and no per-capita tax. Revenue cannot be inferred by comparing land tax alone; population occupations, incomes, taxable coverage and collection efficiency are needed.

## Balance judgment

The evidence favors easing the early tax-collection and research bottlenecks before globally cutting construction goods or raising bureaucracy output. A first balance trial could reduce the base tax-capacity penalty from -80 to -50/-60, make no-metal tax capacity rise modestly with chancery technology, and place the two advanced chancery main methods at distinct appropriate technology ages. Preserve the usefulness of silver/gold alternatives. Consider a small early construction reduction only if budgets remain tight after those changes, and investigate the tier-four local-efficiency drop. These are proposed experiments, not implemented changes or simulation-backed targets.

## Source index

- Mod: `common/goods/uyr_goods.txt`.
- Mod: `common/production_methods/construction_sector_pm.txt`.
- Mod: `common/production_methods/chancery_pm.txt`.
- Mod: `common/production_methods/uyr_optional_luxury_and_minting.txt`.
- Mod: `common/buildings/uyr_goverment.txt`.
- Mod: `common/static_modifiers/aoc_country_modifiers.txt`.
- Mod: `common/static_modifiers/uyr_modifiers.txt`.
- Mod: `common/technology/technologies/30_society.txt`.
- Mod: `common/pop_types/pop_types.md`.
- Mod: `common/defines/aoc_defines.txt`.
- Vanilla: `common/goods/00_goods.txt`, `common/production_methods/13_construction.txt`, `common/production_methods/07_government.txt`, `common/static_modifiers/00_code_static_modifiers.txt`, `common/script_values/building_values.txt`, `common/defines/00_defines.txt`, `common/laws/01_taxation.txt`.

Full recipes, staff counts, reference wages, prices and technology gates: `vanilla_public_cost_comparison.json`.

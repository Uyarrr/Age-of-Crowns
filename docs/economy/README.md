**Age of Crowns: rounded outputs and industrial profit scaling**

The campaign runs from 11 November 1444 through 11 November 1744. Prices come exclusively from the 66 goods in `common/goods/uyr_goods.txt`, including ivory. Existing user edits to both goods files were preserved.

Every custom goods-output quantity is now a multiple of five, including byproduct reductions. Zero-output/off methods remain zero. Inputs remain whole numbers and are adjusted along with outputs to absorb rounding without creating accidental windfalls. Percentage modifiers, innovation, construction points, and other non-goods benefits retain their appropriate units.

All 18 numbered production-method and production-method-group files remain byte-for-byte equal to their pre-task Git versions. No generated override changes those vanilla PMs. Construction material quantities/costs, profession wage weights, and the reduced port workforce are preserved.

Operating profit now follows agriculture < light industry < heavy industry at comparable production capacity and technology age. The comparison assumes access to all technologies through that era, selects each building's latest available main PM, and tests every available secondary PM combination. It includes actual wages for all employees, including extra staff or labor saved by secondary methods. Profit is normalized to the capacity of 3,000 baseline main-PM jobs, not 3,000 remaining jobs after automation; otherwise labor-saving plows would artificially multiply the comparison. Larger buildings, such as rice farms, are scaled to the same reference capacity.

At each age, the least profitable light-industry configuration exceeds the most profitable agricultural configuration by at least 200 per week per reference capacity. The same minimum separation applies between heavy and light industry. These are base-price profits after an annual reference base wage of 5, adjusted by profession wage weights, before tax and owner distributions.

| Technology age | Agriculture profit range | Light industry profit range | Heavy industry profit range |
|---|---:|---:|---:|
| 1 | 459–789 | 1,004–1,444 | 1,704–2,504 |
| 2 | 479–1,060 | 1,366–2,216 | 2,416–3,326 |
| 3 | 763–1,461 | 1,666–2,934 | 3,210–3,578 |
| 4 | 1,155–1,678 | 1,904–3,084 | 3,334–3,578 |
| 5 | 1,159–2,301 | 2,506–3,786 | 4,106–4,326 |
| 6 | 1,159–2,301 | 2,506–3,786 | 4,106–4,411 |

Heavy industry includes heavy manufacturing, military manufacturing, and shipyards. Raw mining/logging/fishing, services, public buildings, and village cottage production have their own balance rules; they are not classified as industrial factories. State minting and other non-saleable benefits are not counted as private operating revenue. Unchanged vanilla-only production is outside this custom-sector ordering.

The hierarchy is enforced using complete building recipes, not only isolated main PMs. Real named research requirements are preserved. Custom primary PMs that used the generic era-six `behaviorism` placeholder now use the appropriate production-age gate (ages 2, 3, and 5 for the successive upgrades). This prevents industries from being stuck on a starting recipe until the final age, and avoids compensating with an oversized starting output.

Example weekly base-price values for the main PM alone, before wages and secondary PMs:

| Building | PM tier | Input value | Output value | Goods surplus |
|---|---:|---:|---:|---:|
| Wheat farm | 1 | 80 | 900 | 820 |
| Wheat farm | 2 | 320 | 1500 | 1180 |
| Wheat farm | 3 | 600 | 2200 | 1600 |
| Wheat farm | 4 | 1000 | 3100 | 2100 |
| Bakery | 1 | 200 | 1650 | 1450 |
| Bakery | 2 | 530 | 2400 | 1870 |
| Bakery | 3 | 800 | 3300 | 2500 |
| Bakery | 4 | 1290 | 4350 | 3060 |
| Ironworks | 1 | 440 | 2500 | 2060 |
| Ironworks | 2 | 810 | 4500 | 3690 |
| Ironworks | 3 | 1210 | 5000 | 3790 |
| Ironworks | 4 | 1940 | 6500 | 4560 |

Early agriculture retains its hiring buffer. The first wheat PM keeps 3,000 jobs, 45 grain output, and 2 tools input. Later main recipes and ordinary manufacturing remain progressively more profitable. The whole-building wage safety check retains adverse prices (inputs +15%, outputs -15%) and the reference wage of 5; lowering material requirements is preferred to increasing output when paying that reserve.

Ports retain their cheaper staffing: 50 workers at idle anchorage, and 400/500/600 for active tiers. Merchant-marine outputs are rounded to 10/15/20, with 1/2/3 naval supplies as inputs. Caravan hubs have the same staffing/output and use 1/2/3 horses. Existing convoy, infrastructure, and English sailor effects remain. An idle anchorage incurs maintenance wages and has no saleable output; it is not forced to make a commercial profit.

Ivory remains a buildable luxury resource at price 60, with optional furniture/jewelry PM groups, separate from the existing fur/gold choices. Quantized ivory recipes are:

| Optional PM | Ivory input | Output | Input value | Output value | Added surplus |
|---|---:|---|---:|---:|---:|
| Furniture 1 | 2 | 5 luxury furniture | 120 | 300 | 180 |
| Jewelry 1 | 4 | 5 jewelry | 240 | 450 | 210 |
| Furniture 2 | 4 | 10 luxury furniture | 240 | 600 | 360 |
| Jewelry 2 | 9 | 10 jewelry | 540 | 900 | 360 |

The small first-tier difference follows from whole ivory inputs and five-unit finished goods; both advanced variants add the same surplus. Ivory processing unlocks in production ages 2 and 4, and each group retains a free off option.

Chancery gold minting remains optional and separate from silver. The tiers consume 2/4 gold for 30/70 tax capacity and 15/35 bureaucracy. Silver consumes 3/5 silver for 20/40 tax capacity and 10/20 bureaucracy. At gold price 100 and silver price 60, gold costs more in total and grants more benefits, with improved benefit per cost. Public-service upgrades are checked by input cost per principal benefit, not invented goods revenue.

The corrected pop needs and 99 wealth spending packages remain in place. Books, medicine, chocolate, wax, fur, and actual military demand remain represented. Ivory is an industrial luxury input rather than a compulsory pop purchase.

Validation covers 351 reachable custom PMs and 1,270 general PM combinations. Checks pass for multiples-of-five outputs across every custom PM file, integer recipe quantities, referenced goods/technologies, positive saleable margins, increasing upgrade profits with wages, nonnegative combined outputs/employment, wage/price stress, and the sector hierarchy at all six ages. The authoring policy also passes a repeat-run idempotence check. Preserved vanilla dependency warnings remain separately recorded in `audit.json`.

This is static validation, not a game launch or AI save simulation. Actual regional demand, shortages, hiring qualifications, wage levels, local prices, throughput, ownership, and the full market-price range can change realized profits and sector ordering. The calculated hierarchy applies to the stated price/wage scenario, not every possible market state.

Review files: `sector_profits.csv` contains age-by-sector ranges; `sector_combinations.csv` contains the underlying complete recipes; `production_methods.csv`, `buildings.csv`, `goods.csv`, `public_benefits.csv`, and `pop_budgets.csv` provide full audit data. `industry_scaling_before.csv` records recipes before this pass, and `hiring_before.csv` records the earlier hiring baseline.

Run `python tools/economy_audit.py --write-report` for read-only validation/report refresh. Run `python tools/rebalance_economy.py --apply` only to intentionally reapply the authoring policy. Set `VICTORIA3_GAME_DIR` to the installed Victoria 3 `game` directory on another installation.

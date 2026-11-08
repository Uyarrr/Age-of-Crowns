# Coinage, administration and precious-metal balance

Implemented 6 November 2026. This supersedes the earlier proposal in vanilla_public_cost_comparison.md; that file and its JSON are a pre-change historical comparison.

## Design

Vanilla-sized tax capacity and similar public cost per bureaucracy, with paper and bullion sharing the output. The no-metal office remains functional; imported or domestic bullion enables the efficient path. Both minting groups grant bureaucracy AND tax capacity. Gold is available through the era-one minting_house technology; advanced silver accompanies era-two paper; advanced gold requires production age four. Paper upgrades use formalized_administration (2), printing_press (3), administrative_suzerainty (4).

Base state tax capacity is restored to vanilla 100 by removing the mod -80 injection. Other global modifiers and construction recipes are unchanged. Existing PM IDs and staffing remain; existing saves retain their chosen PM IDs. A previously selected advanced method can now require research that the country lacks; recheck those offices after loading.

| Main office | Bureaucracy | Tax capacity | Paper/week | Books/week |
|---|---:|---:|---:|---:|
| 1 | 20 | 2 | 0 | 0 |
| 2 | 35 | 6 | 8 | 0 |
| 3 | 45 | 10 | 7 | 2 |
| 4 | 55 | 20 | 7 | 3 |

| Coinage group | Metal/week | Bureaucracy | Tax capacity |
|---|---:|---:|---:|
| Silver 0 | 0 | 0 | 0 |
| Silver 1 | 3 | 15 | 2 |
| Silver 2 | 5 | 30 | 4 |
| Gold 0 | 0 | 0 | 0 |
| Gold 1 | 2 | 15 | 3 |
| Gold 2 | 3 | 25 | 6 |

All outputs stack across the main, silver and gold groups. Off methods contribute zero. Maximum office output is 110 bureaucracy and 30 capacity, compared with vanilla 100 and 30. This replaces the old potential 155 bureaucracy and 110 capacity. Main output is deliberately lower than before because minting now supplies part of the normal administrative output, rather than a large extra tax-capacity bonus.

## Complete office comparisons

Full employment, base goods prices, annual reference base wage 5; hereditary/religious staffing includes all 1,500 employees, with £456.73 weekly wages. Public aristocrats receive wages: paid_private_wage=no only excludes wages in private buildings. No scale, law, shortage, government-wage-setting or local-price modifiers.

| Stage | Mod bureaucracy / tax | Mod weekly cost | Vanilla bureaucracy / tax | Vanilla weekly cost | Mod cost per bureaucracy vs vanilla |
|---|---:|---:|---:|---:|---:|
| 1 | 50 / 7 | £836.7 | 50 / 10 | £756.7 | +10.6% |
| 2 | 80 / 13 | £1,196.7 | 50 / 10 | £756.7 | -1.2% |
| 3 | 90 / 17 | £1,256.7 | 65 / 15 | £1,056.7 | -14.1% |
| 4 | 110 / 30 | £1,401.7 | 100 / 30 | £1,406.7 | -9.4% |

These use both available metals, not a claim every country can source both. Silver-only starting administration supplies 35 bureaucracy / 4 capacity at £636.73, versus its former 30 / 20 at the same cost. No-metal outputs are the main office table above. All four available profession/religion staffing combinations are represented in the JSON configuration data; all calculations exclude throughput.

## AI

Both silver and gold groups explicitly use the documented most_productive selection mode; gold previously defaulted to most_profitable. Each active coinage method carries both services, each upgrade improves service per bullion cost, and both off methods remain valid. No fixed high AI weight or event forces countries to buy metals. These definitions expose the intended benefits to the engine; import decisions, affordability and actual AI adoption require an in-game campaign check. The authoring tool does not claim to simulate the engine AI.

## Precious-metal mines

Main mine output follows a common upgrade pattern: ordinary mines 25/45/65/90, silver and gold 20/35/50/70 (the same approximate multipliers, rounded to fives). Main tool consumption is 3/8/14/22 for all nine mines. Existing staffing, research gates, secondary methods and base goods prices remain. Existing treasury bonuses remain separate; the missing third silver bonus is repaired to 1,200. Mine profit below EXCLUDES treasury minting: money paid to the country is not factory wage revenue.

| Mine | Tier | Output before → after | Private profit before → after | Stress profit after |
|---|---:|---:|---:|---:|
| silver | 1 | 15 → 20 | £514 → £734 | £104 |
| silver | 2 | 30 → 35 | £876 → £1,416 | £286 |
| silver | 3 | 40 → 50 | £1,284 → £2,004 | £364 |
| silver | 4 | 60 → 70 | £1,826 → £2,866 | £546 |
| gold | 1 | 10 → 20 | £534 → £1,534 | £504 |
| gold | 2 | 15 → 35 | £856 → £2,816 | £986 |
| gold | 3 | 25 → 50 | £1,264 → £4,004 | £1,364 |
| gold | 4 | 35 → 70 | £1,806 → £5,666 | £1,946 |

Stress means metal sale prices -50%, input prices +25%, annual base wage 5. Every main + transport combination and gold fields remains profitable in that scenario, and every mine upgrade increases base-price private profit. The wider CSV deliberately includes losing scenarios at still worse prices/higher wages: this is not guaranteed profit at the full ±90% market range.

Starting output remains 25 for ordinary mines (coal, stone, iron, copper, tin, lead and gems) and 20 for silver and gold. Coal/stone previously produced 35 because an older policy targeted similar sale values across resources; the new policy preserves consistent quantities instead. Cheaper resources have lower profits. Complete recipes improve both base-price and adverse-price private profit at every main upgrade; see mine_upgrade_progression.csv for every attached secondary configuration. The ordinary-mine adverse scenario uses outputs -15%, inputs +15%, reference annual base wage 5.

Gold fields output increases 5 → 10, retaining 1,000 jobs and their existing 250 treasury minting; these smaller, non-buildable fields are separate from mines. A tier-one silver mine produces 20 silver: enough for 6.7 basic-silver offices. A tier-one gold mine produces 20 gold: enough for 10 basic-gold offices. At the final tier, mines supply 14 advanced-silver offices or 23.3 advanced-gold offices. Other industrial bullion demand competes for that supply. Demand, prices and trade still determine realized income; larger supply alone cannot guarantee a price floor. The larger advanced-gold output warrants observing late-game demand and prices in a campaign.

## Verification and maintenance

Checked 144 office configurations, 16 precious-mine/transport configurations plus gold fields, 612 mine price/wage scenarios, and 88 complete mine-upgrade configurations across nine resources. Vanilla unit-cost comparisons, bullion efficiency, technology gates, defined professions and both service outputs are checked by tools/audit_minting.py. The general economy audit separately checks the mod's recipes and sector ordering.

Run `python tools/audit_minting.py --write-report` and `python tools/economy_audit.py`. Reapply the policy with `python tools/balance_minting.py --apply`; the general rebalance calls the same policy last so that it cannot silently undo these targets.

Remaining verification: launch with the mod, check tax-capacity tooltips, inspect the AI's coinage selections/imports and mine hiring in a campaign. No game launch or campaign simulation was performed here. Existing unrelated vanilla-dependency warnings remain outside this change.

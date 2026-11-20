# Age of Crowns modding notes

## Victoria 3 metadata replacement paths

- In `.metadata/metadata.json`, list every directory being replaced in `game_custom_data.replace_paths`. Victoria 3 applies each entry only to files directly inside that directory. Keep `events` and each vanilla event subdirectory listed explicitly. Before deleting a same-path override, verify that its immediate parent directory is listed, including for DLC content.

## Journal entries in the lobby

- Every journal entry with `is_shown_in_lobby` needs an English `<journal_entry_key>_lobby` localization. Keep it to one or two concise, distinct sentences that introduce the situation and objective without repeating the full journal description.

## Journal country pickers

- For decisions that ask the player to choose a country, follow the Papal Bulls picker. Build the list from eligible targets in alphabetical order, use three columns, and show each country's flag and name with `[Country.GetName]`. Apply this to invitations, influence, subject titles, and appanage promotion.
- Share the gameplay eligibility trigger between list generation and scripted GUI validation. Hide stale or ineligible rows and recheck eligibility when the player selects a target.

## Victoria 3 country events

- Time historical events by research progress instead of calendar dates. Use `aoc_era_research_early`, `aoc_era_research_mid`, or `aoc_era_research_late` with `{ ERA = 3 }` for Discovery or the matching era number for another age. These milestones begin at 25%, 50%, and 75% and remain met as research advances. They count regular technologies across Production, Military, and Society, excluding age unlocks and automatically granted national technologies.
- For era-timed events in every nation, combine the entry milestone with `aoc_era_event_window_open` for the same era. This window closes at 100% of that era's regular technologies. Age unlocks have no effect on the window, and the event timing rule does not change technology prerequisites.
- Use a dedicated child on-action with `random_events` for chance-based scheduling and `fire_only_once = yes` for unique events.
- Follow vanilla country events such as `iberia.11` and the Balkan League chain. Give the event a short title, report what changed in the description, and use `flavor` for a brief scene in the period’s voice. For shared news, use a single in-character acknowledgement that fits every recipient.
- Keep event descriptions, flavor, and option labels distinct and free of mechanical effects or modifier text. Show gameplay effects through the scripted options and their tooltips. For historical choices, use AI weights of 80 and 20 when two options are available.
- Save country scopes before dispatching a popup and use `[SCOPE.sCountry('scope_name').GetName]` in localization. Use `popup = yes` for news meant to open on arrival.
- Put English event strings in the existing nation-content localization file when one exists, using UTF-8 with BOM. Add player-facing timing to `tools/nation_event_catalog.json` when the generated Events tab needs to explain research milestones or random odds. Keep simple option modifiers as direct `add_modifier` effects so the journal generator can render the modifier name, duration, and effects.
- Put a short historical briefing under each title in the Events tab. Add a one-sentence `briefing` to `tools/nation_event_catalog.json` when the full description is too long or uses event scopes. Keep research requirements and firing odds in the tooltip's “When it can happen” section.
- Sort events within each viewer section by age, then by research milestone. Put events without a known age last.
- Run `Update Nation Content.cmd` or `node tools/build_nation_content.cjs` after changing events or technologies. The updater rebuilds era research totals and the Events tab, and records event visibility with a seen marker. Verify generated files with `node tools/build_nation_content.cjs --check` and check the event row and option tooltips in game after relaunching.

## French historical event draft balance

- Use these rules when implementing the eighteen proposed French events, three per age. Apply them to existing historical content when a later task requests that rebalance.
- French Traditions events retain their Era 1 entry milestones and remain eligible until France reaches 50% of regular Renaissance (Era 2) research. Use `aoc_france_traditions_window_open = yes` for this exception, including the existing Francs-Archers event. Later ages retain the normal window closing at full research for their own era.
- Give historical event modifiers a duration of ten years, including penalties and interest-group approval modifiers. Use `years = 10` on the effect that applies the modifier.
- Use these baseline magnitudes for historical event rewards. Trade Capacity is +15%, Trade Advantage is +15%, Conversion Speed is +10%, Assimilation Speed is +10%, flat Infrastructure is +10, percentage Infrastructure is +15%, and nationwide Education Access is +5 percentage points.
- Multiply state-specific rewards by three. A modifier applied to a specific state gives +45% Trade Capacity, +45% Trade Advantage, +30% Conversion Speed, +30% Assimilation Speed, +30 flat Infrastructure, +45% Infrastructure, or +15 percentage points of Education Access. Choose the appropriate flat or percentage Infrastructure reward for the event. Apply the multiplier once based on the actual recipient scope. A country modifier using a `state_` modifier key still uses the national baseline.
- For army-wide combat rewards, give +5% Offense and +5% Defense when both are included. A reward affecting only Offense or only Defense gives +10% to that stat.
- For a specific troop type, use a combined bonus budget of 20 percentage points across its combat stats. Examples are +20% Offense, or +10% Offense and +10% Defense. Other troop combat stats may share the same total budget. These troop-specific values already account for their narrower scope.
- Interest-group approval and disapproval are +3 and -3 for ten years. These are country-level political effects and keep their magnitude when accompanying a state reward.
- Scale historical event money costs to the paying country's weekly gross income using `fixed_income`, clamped to zero or greater. Small costs equal one week of income, standard costs two weeks, and major costs four weeks. Standard costs are the default. Calculate the amount when the option is taken, in the payer's country scope, and display the same calculation in its tooltip. Use a one-time treasury payment for ordinary event costs.
- Vanilla references for money scaling are `common/script_values/event_values.txt` (`money_amount_multiplier_*`, based on GDP), `common/script_values/ip4_je_values.txt` (`yearly_gross_income`, using `fixed_income * 52`), and `events/expedition_events/antarctic_expedition_events.txt` (an expense modifier with a script-value multiplier). The income-based cost tiers above are Age of Crowns balance choices.

## Hundred Years’ War

- Keep journal involvement separate from military support. French appanages start involved and neutral. Country actions should use explicit actor and target checks. A French subject must have France as its overlord, and France itself is excluded.
- Announce new military support from the shared roster refresh after it updates journal involvement. Establish the initial roster silently and announce each later change to a supported crown once.
- Outside countries participate through valid support. Keep the withdrawal cooldown shared between treaty and invitation support. Recheck relations and active enemies when reviewing pledges and answering summons. Use `change_subject_type` on the direct French vassal for promotion.
- For Invite to War, require the inviting crown to have Engaged or higher interest in the target capital's strategic region. The target can have any interest tier in the crown's region. Apply the check to the picker, AI invitations, and invitation acceptance.
- Block ordinary diplomatic plays between participants in the play's `possible` trigger before launch. Keep the scripted campaign exempt. Use the [Hundred Years’ War notes](docs/hundred_years_war.md) for the implementation and in-game checks.
- Center icon-and-value groups using content-sized text inside a centered container. See the [journal UI guide](docs/journal_entry_gui.md).

## Victoria 3 modifier tooltips

- When an action previews a static modifier, render its actual effects in localization with `[GetStaticModifier('modifier_key').GetDesc]`. Use the same key as the gameplay script's `add_modifier` so the tooltip tracks balance changes and uses the game's modifier labels and formatting.
- Put the recipient and duration above the generated effects, and any cost or cooldown below. See the Dei Gratia Rex and Illius Qui Se Pro Divini tooltips in `localization/english/aoc_catholic_church_l_english.yml`.
- Set papal modifier icons in `common/static_modifiers/aoc_country_modifiers.txt` to `gfx/interface/icons/religion_icons/catholic.dds`.

## Catholic Church UI

- Pin the global Church journal for Catholic members with `should_be_pinned_by_default_involved = yes` in `common/journal_entries/aoc_catholic_church.txt`.
- The Money tooltip splits Catholic Tithe out of Additional Expenses. Keep the actual budget charge, the displayed amount, and the Church ledger tied to the same stored weekly rate. Hiding the timed modifier from the country panel is a UI change.
- In the Money tooltip, close all formatting around the amount before rendering the title. The tithe row uses `#tooltippable_concept $aoc_church_budget_tithe$#!` for the vanilla gold style. Check the rendered tooltip in game after changing markup.

## Historical localization

- Write concise, period-appropriate descriptions in the style of Victoria 3. Give technologies, laws, units, and buildings distinct historical flavor. Leave mechanical effects to their tooltips.

## Building inputs and markets

- Assess starting building inputs against supply in the owner's national market. Use goods the market can produce or import in the relevant age, and compare base-price upkeep and wages with buildings that serve a similar role.
- For national monuments with a defined unlock age, use the matching construction cost in `common/script_values/aoc_monument_construction.txt`. Give monuments larger workforces and greater goods demand than comparable ordinary buildings, with at least one distinctive benefit that remains useful in the Age of Revolutions.

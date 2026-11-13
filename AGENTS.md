# Age of Crowns modding notes

## Journal entries in the lobby

- Every journal entry with `is_shown_in_lobby` needs an English `<journal_entry_key>_lobby` localization. Keep it to one or two concise, distinct sentences that introduce the situation and objective without repeating the full journal description.

## Journal country pickers

- For decisions that ask the player to choose a country, follow the Papal Bulls picker. Build the list from eligible targets in alphabetical order, use three columns, and show each country's flag and name with `[Country.GetName]`. Apply this to invitations, influence, subject titles, and appanage promotion.
- Share the gameplay eligibility trigger between list generation and scripted GUI validation. Hide stale or ineligible rows and recheck eligibility when the player selects a target.

## Victoria 3 country events

- Follow vanilla country events such as `iberia.11` and the Balkan League chain. Give the event a short title, report what changed in the description, and use `flavor` for a brief scene in the period’s voice. For shared news, use a single in-character acknowledgement that fits every recipient.
- Save country scopes before dispatching a popup and use `[SCOPE.sCountry('scope_name').GetName]` in localization. Use `popup = yes` for news meant to open on arrival.

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

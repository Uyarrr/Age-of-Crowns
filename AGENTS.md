# Age of Crowns modding notes

## Journal entries in the lobby

- Every journal entry with `is_shown_in_lobby` needs an English `<journal_entry_key>_lobby` localization. Keep it to one or two concise, distinct sentences that introduce the situation and objective without repeating the full journal description.

## Victoria 3 modifier tooltips

- When an action previews a static modifier, render its actual effects in localization with `[GetStaticModifier('modifier_key').GetDesc]`. Use the same key as the gameplay script's `add_modifier` so the tooltip tracks balance changes and uses the game's modifier labels and formatting.
- Put the recipient and duration above the generated effects, and any cost or cooldown below. See the Dei Gratia Rex and Illius Qui Se Pro Divini tooltips in `localization/english/aoc_catholic_church_l_english.yml`.
- Set papal modifier icons in `common/static_modifiers/aoc_country_modifiers.txt` to `gfx/interface/icons/religion_icons/catholic.dds`.

## Catholic Church UI

- Pin the global Church journal for Catholic members with `should_be_pinned_by_default_involved = yes` in `common/journal_entries/aoc_catholic_church.txt`.
- The Money tooltip splits Catholic Tithe out of Additional Expenses. Keep the actual budget charge, the displayed amount, and the Church ledger tied to the same stored weekly rate. Hiding the timed modifier from the country panel is a UI change.
- In the Money tooltip, close all formatting around the amount before rendering the title. The tithe row uses `#tooltippable_concept $aoc_church_budget_tithe$#!` for the vanilla gold style. Check the rendered tooltip in game after changing markup.

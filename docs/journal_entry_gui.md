# Journal entry GUI in Age of Crowns

Source checked against the installed Victoria 3 1.15.1 build. Paths in the vanilla references are relative to the game's `game/` directory. The game ships the attachment contract in `common/journal_entries/journal_entries.md` and implements it in `gui/journal_entry.gui`.

## Choose the smallest extension point

- Use the journal entry definition for status, activation, outcomes, and their tooltips. Use `scripted_button` for ordinary actions and `scripted_progress_bar` for tracked meters. The stock panel supplies the controls, tooltips, and progress display. See the shipped notes in `common/scripted_buttons/` and `common/scripted_progress_bars/`. In this mod, `je_england_2` uses both.
- Add a named widget for content that needs its own layout, such as a portrait header, roster, or ledger. Put the widget in a dedicated `gui/journal_entry_widgets/aoc_*.gui` file and attach it from the journal entry. This works with the stock panel and leaves the attachment local to the entry.
- Changes to the shared panel itself start from the current vanilla `gui/journal_entry.gui`. Vanilla's `gui/scripted_widgets/` startup registration is a separate facility for widgets instantiated at startup.

## Attach a widget

Inside the journal entry:

```pdx
widget = {
    gui = "gui/journal_entry_widgets/aoc_example.gui"
    name = "widget_aoc_example"
    container = "custom_widget_container_3"
}
```

In that GUI file, declare a top-level widget with the matching `name`:

```pdx
flowcontainer = {
    name = "widget_aoc_example"
    direction = vertical
    spacing = 6

    textbox = {
        autoresize = yes
        text = "aoc_example_widget_label"
        using = fontsize_small
    }
}
```

Define `aoc_example_widget_label` in localization. A journal entry can declare multiple `widget` blocks. The stock panel renders them for the active entry. The concluded view uses the localized title and the outcome's `conclusion_desc`. Supply a static `<journal_entry_key>_concluded` title when the active title depends on scope. For any entry with `is_shown_in_lobby`, add a concise, distinct English `<journal_entry_key>_lobby` description.

| Container | Placement in the stock panel |
| --- | --- |
| `custom_widget_container_je_icon` | Replaces the standard journal illustration and icon header |
| `custom_widget_container_1` | Below the header, before the early timeout and status area |
| `custom_widget_container_2` | Between status and buttons |
| `custom_widget_container_buttons` | Replaces the standard scripted-button row when an attachment is registered |
| `custom_widget_container_3` | After buttons, before scripted progress bars |
| `custom_widget_container_4` | After scripted progress bars, before the description |
| `custom_widget_container_5` | After the description, before involved countries |
| `custom_widget_container_6` | After involved countries, before the progress and outcome area |
| `custom_widget_container_7` | After the progress and outcome area |

## Layout and data

- Use `flowcontainer`, `vbox`, or `hbox` for sections whose content can grow. Use spacing, margins, and layout policies for alignment. Vanilla mixes flow layout with fixed-size portrait and icon compositions. Check the host panel width before sizing a grid or card, and allow localized labels to wrap or elide.
- Look in `gui/shared/` for reusable flags, portraits, buttons, dividers, backgrounds, and progress bars. Instantiate a shared type and customize its named blocks with `blockoverride`. Use `using` for named styles or templates such as `fontsize_small`. Put repeated custom rows in a prefixed `types` declaration.
- The active detail pane supplies `JournalEntry`. Read entry-owned variables and lists through `JournalEntry.MakeScope`. For a country-owned list, Meiji uses `JournalEntry.GetCountry.MakeScope.GetList('daimyos_list')`. A contextless entry can lack an owning country. Use entry-owned scopes for shared data and `GetPlayer` when the expression specifically needs the viewing country.
- Feed repeated rows with `datamodel` and bind each row's object with `datacontext`. Meiji passes scope-list items to a reusable character row that uses `[Scope.GetCharacter]` and checks validity. Use `IsDataModelEmpty` for empty states and validity checks before displaying optional countries or characters.
- Keep gameplay conditions and effects in scripts. For a custom control that needs an explicit actor and row target, use a scripted GUI and pass the same `GuiScope` to eligibility and execution. The Church relief picker sets the player as root and passes the selected country with `AddScope`. Vanilla Meiji uses `GetVariableSystem.Toggle` for its local expand/collapse state.

## Examples to copy

| Vanilla entry and GUI | Pattern |
| --- | --- |
| `00_meiji_restoration.txt` → `ep2_japan_widgets.gui` | A custom header plus a separate collapsible daimyo list in slot 3. The list uses a reusable row and stock section header. |
| `00_player_objectives_great_game.txt` → `great_game_widgets.gui` | A slot 3 widget that lists active entries through the journal group datamodel. |
| `00_rlit_journal_entries.txt` → `rlit_widgets.gui` | Two entries reuse one slot 4 widget. Named blocks configure the route rows, and a scripted GUI checks which route leads. |

The Hundred Years’ War uses slot `custom_widget_container_je_icon` for its illustrated header and supporter flags, and slot `custom_widget_container_3` for its action pickers. Its emblem sits above the two crowns. The battalion and flotilla rows use 32-pixel icons with auto-sizing numbers in a centered flow container beneath each flag.

For a country picker, use the Papal Bulls layout. Generate an alphabetized list of eligible countries, use three columns, and display `[Country.GetName]` for the flag and name. The Church and war pickers share `aoc_for_each_country_by_english_name` for defined tags. The war picker appends eligible dynamic tags after the ordered entries. Reuse the same eligibility trigger for list generation and execution, and hide stale rows in the UI.

After changing a widget, open its active journal in game and inspect the layout at the UI scales you support. Check empty and populated lists, long names, missing optional scopes, action availability and tooltips, and the concluded view. For a contextless journal, check from each relevant country. Review new messages in `logs/error.log` under the Victoria 3 user directory for widget, binding, or localization errors.

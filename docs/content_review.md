# English content and journal review — Victoria 3 1.15

The review covers all 75 local English localization files structurally, and the
live journal, event, button and progress-bar scripts. Most of the roughly 217,000
English entries are converted personal and place names; these have not been
individually rewritten. 105 existing text keys were revised, alongside new
Ming, journal-conclusion and South American country text.

## Writing

Event descriptions now state the situation and decision. Flavour text supplies
a brief scene instead of repeating the description. The longest English event
passages, including inherited converter overrides, were condensed. Decisions
use specific verbs, and journal instructions distinguish narrative from
mechanical requirements. No live journal narrative exceeds 85 words.

Council text states its £1,000 weekly cost, three-year duration and four-year
interval. Patronage descriptions explain the shared three-year lock. The
dynastic settlement tooltip gives the thresholds and current counters without
the former calendar essay. Corrected misleading choice labels, enclosure's
assumed overseas migration, the premature account of York's death, and generic
voyage text tied unnecessarily to Cartier's historical lifetime.

## Compatibility and logic

The installed `game/common/journal_entries/journal_entries.md` explicitly
retires `complete/on_complete`, `fail/on_fail`, `invalid/on_invalid`, and the old
outcome-description fields. Every mod journal now uses 1.15 `outcome` blocks,
with activation descriptions, localized conclusion text, and hidden invalid
outcomes where needed. Button-only journals deliberately have no automatic
completion. The old two-sided progress-bar preset is replaced with explicit
textures; conditional factors use the current `progress_condition` format so
the journal can show their requirements.

* The Hundred Years' War now calls victory event `england.300` and defeat event
  `england.301`. It previously called the unrelated justice/office events.
  Objectives count distinct French state regions, including subject holdings;
  defeat also handles complete loss of continental possessions.
* The Great Council explicitly rejects both its active modifier and a timed
  country flag. The modifier check covers existing saves without the new flag;
  the flag enforces the full four-year interval after a new summons.
* The Wars of the Roses has no calendar gates. Renaissance research or serious
  unrest begins the Royal Crisis. Tension, the protectorate, prior confrontations,
  actual wars, and player choices govern subsequent episodes. A common
  eight-month narrative interval prevents several episodes arriving together.
* A victorious dynasty can settle after 24 consecutive months at Tension ≤30,
  no revolution, and firm support (Lancaster ≥65, York ≤35). Without a dynastic
  war, Lancaster needs 36 months at Tension ≤20 and support ≥65 after the Royal
  Crisis begins. Interruptions reset these counters. Tudor victory still settles
  the conflict immediately. There is no mandatory second war or late-date shortcut.
* Both incumbent and rebel victories now set Tension to 25 and support to 70
  for Lancaster or 30 for York. Removing the high-tension penalty gives both
  winners an equal opportunity to consolidate; civil-war exhaustion still applies.
* Ruler selection follows the actual succession choices instead of historical
  death dates. A victorious Edward is no longer replaced by a recreated Richard
  in the accession event. The princes episode requires Edward's branch. An English
  successor formed through civil war retains eligibility for overseas journals.
* Administrative and enclosure events now use research and political context;
  yearly fallback callers make their choices available even when a country starts
  with the relevant technology.
* Ming's converter journal called three nonexistent Boxer/Warlord events and
  relied on uninitialized variables and nineteenth-century conditions. It is
  replaced by **The Ming Mandate**: three years of independent, peaceful government,
  Legitimacy ≥60, no borrowing or revolution, incorporated-state Turmoil below
  25%, and Renaissance research remove the existing Troubled Empire modifier.
  This is a governance challenge, not a restored nineteenth-century fragmentation
  chain. No arbitrary calendar deadline is introduced.

## Validation

Run from the mod root:

```powershell
node tools/audit_content.cjs
node tools/audit_england_overseas.cjs
node tools/audit_south_america.cjs
node tools/audit_map_1_15.cjs
```

The content audit checks local English formatting, reachable localization and
event references, research keys, assets, retired journal fields, narrative
lengths, and the actual council and dynastic-stability triggers. The overseas
audit retains its reward, charter, timer and ownership tests. Its texture check
now accepts validated BC3/BC7 DX10 headers as well as DXT5, matching the assets
already in the repository.

All checks are static or scripted simulations. No Victoria 3 campaign has been
loaded or played during this review. Journal rendering, event delivery and AI
balance still need an in-game check on 1.15. Start a new campaign for the map and
startup-history changes; existing saves keep their stored territories and people.

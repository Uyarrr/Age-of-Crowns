# North America in 1444

The mainland US/Canada setup now has **22 playable, centralized factions** and
**eight decentralized regional tags**, replacing 86 active tags across 61 states.
Centralized factions use `country_type = unrecognized`, incorporated territories,
animist religion, and explicit startup laws using the mod's law definitions.

| Region | Playable factions |
| --- | --- |
| Pacific Northwest | Tlingit (TLG), Haida (X01), Chinook (X83) |
| West | Shoshone (SHH), Ute (UTE), Chumash (CMS) |
| Southwest | Rio Grande Pueblos (PUE), Hopi (HOP), Zuni (ZUN) |
| Great Plains | Dakota (DKT), Pawnee (PWN), Osage (O01) |
| Great Lakes / Canada | Cree (CRY), Ojibwe (OJB), Wendat (WDT) |
| Northeast | Iroquoian Nations (IRO), Lenape (L03), Mi'kmaq (MKQ) |
| Southeast | Cherokee (CHE), Choctaw (C03), Caddo (C05), Calusa (CLS) |

Other owners merge by geography into Pacific Northwest Peoples (NPA), Western
Peoples (NWE), Southwestern Peoples (NSX), Great Plains Peoples (NGP), Great Lakes
and Boreal Peoples (NGL), Northeastern Peoples (NNE), Southeastern Peoples (NSE),
and Arctic and Subarctic Peoples (NAQ). Each category uses a single country tag
across its states. Redundant split states are combined by their new owner.

Cree now uses its own `CRY` tag and banner, with a compact 37-province James Bay
core. Its former western boreal territory is decentralized, including autonomous
Cree bands. Hopi (9 provinces) and Zuni (8 provinces) are separate playable
countries; the Rio Grande Pueblos retain a connected 15-province core.

Cree and the Iron Confederacy remain separate identities. `IRC` is reserved for the later
**Iron Confederacy**, which has no provinces or country history at the start.
It is a normal country formable for Cree or Ojibwe: independent, at peace,
with Nation Formation and Iron Weapons researched, and the normal formation
control requirement met in two of Alberta, Saskatchewan and Manitoba. The target
is kingdom-tier and includes the existing Cree, Siouan (representing Assiniboine)
and Algonquian culture groups. The tech gate supports alternate-history timing;
there is no fixed calendar-year requirement or forced historical event.
English names and adjectives are explicitly overridden in
`localization/english/replace/zz_aoc_north_america_l_english.yml`.

This is a political gameplay abstraction. Iroquoian Nations is one playable
umbrella faction; Wendat remains separate. Existing broad culture groups remain
in use, so several factions share cultures. Territories now use source-linked
homeland and ancestral settlement research, traced against the game's province
bitmap. See [the research notes](north_america_1444_research.md) for evidence,
uncertainty, and each faction's assigned regions. New banners are abstract
gameplay designs, not historical flag reconstructions.

Playable factions own province-level portions of states; none owns an entire
state region. Southern Delaware remains decentralized for Nanticoke-related
representation; a peripheral New Jersey province represents autonomous Lenape
bands within Northeastern Peoples. This avoids inventing a non-Lenape enclave
just to satisfy the no-whole-state rule. Research informs the settlement cores;
exact 1444 political frontiers cannot be established for every faction.

Mexico, Mesoamerica, the Caribbean, Hawaii, and Bermuda keep their existing
ownership. Unused old country definitions remain available for scripts and
releasables; they do not have mainland starting states. Relations involving the
69 old tags that no longer own any starting territory have been removed from
the converted relations history.

All **8,059 distinct provinces** and **3,120,593 population** in scope are
preserved. Population culture, religion, and pop type are preserved per state.
Where an old state region splits between new owners, its pops are apportioned
by province count, with rounding remainders retained. Existing duplicate province
assignments are resolved once, favoring selected factions. Orphan population
scopes move to an existing owner in the same state. Building scopes follow the
new ownership.

Run `python tools/audit_north_america.py` to check tag counts, unique definitions,
province coverage, population totals and composition, owned capitals, culture
and startup-law references, and population/building ownership scopes.
`north_america_baseline.json` records the pre-migration coverage and population.
`north_america_1444_provinces.json` records every final province assignment.
`tools/refine_north_america_1444.py --apply` regenerates these assignments from
the reviewed profiles in `tools/north_america_1444_homelands.json`; it preserves
population composition and uses exact, unsampled province pixel centroids.
The original consolidation script is retained as migration history; its broad
geographic bands are superseded by the research profiles.

Static validation passes. A new-game launch is still needed to verify the
country selection screen, rendered map, flags, and runtime error log. Performance
has not been benchmarked; the active country count in scope falls from 86 to 28.

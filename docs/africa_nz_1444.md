# African and New Zealand consolidation

Africa has 68 active owners instead of 143. Three regional tags are decentralized:
`AFD`, Northern and Western African Peoples; `AFC`, Central African Peoples;
and `AFE`, Eastern and Southern African Peoples. Former decentralized territory
outside the selected playable tags is divided between these regions.
Existing centralized owners retain their territory. Country
definitions use explicit/conditional assignment precedence, so a converter's
`?=` fallback does not override an earlier explicit definition.

These 33 selected tags are playable, with incorporated territory and startup
government laws matching the existing indigenous playable setup:

| Area | Selected countries and peoples |
| --- | --- |
| West Africa | Mali, Bornu, Jolof, Benin, Oyo, Songhai, Yatenga, Wagadugu, Asante, Dahomey |
| Central Africa | Kongo, Luba, Lunda, Kuba, Azande, Wadai |
| Great Lakes | Buganda, Bunyoro, Rwanda, Burundi |
| Swahili coast | Kilwa, Sofala, Pate, Mombasa, Malindi |
| Southeast and Madagascar | Mutapa, Butua, Maravi, Sakalava |
| Southern and pastoral peoples | Zulu, Xhosa, Tswana, Maasai |

This is a mixed historical/gameplay selection under the request to represent
important peoples in 1444 **or more generally**. It is not a claim that every
selected kingdom existed in 1444 with these borders. Mali, Benin, Kongo and the
Swahili towns provide medieval anchors. Later formations such as Asante,
Dahomey, Luba, Lunda, Kuba and the Zulu kingdom are retained as generally
important playable representations. Existing province footprints are used;
this migration does not reconstruct period borders or dynasties.

Oyo gains Yoruba as a primary culture alongside the inherited Edo group; Kilwa
gains Swahili alongside the inherited Yao group. Muslim court religions are
initialized for Mali, Bornu, Jolof, Songhai, Kilwa, Sofala, Pate, Mombasa,
Malindi and Wadai. Existing pops keep their cultures and religions.

The three regional tags are optimization aggregates, not historical states.
Each accepts the cultures of its regional populations. Retired
tags retain their definitions but no longer own territory in the affected
region. Retired countries' diplomatic clauses are removed instead of
transferring their feuds to the aggregates. The lower country count is verified;
game performance has not been benchmarked.

New Zealand has two owners:

- `NPH`, Ngāpuhi: six Northland provinces formerly assigned to T75, playable
  and incorporated. The tag represents a small northern Māori starting point;
  use of the later collective identity in 1444 is a gameplay abstraction.
- `MZD`, Māori Peoples: all other North Island and South Island territory,
  decentralized. This replaces the remaining five North Island owners and
  the South Island owner with one aggregate.

PUE's displayed English name is now **Pueblo**; the supporting migration and
North American notes use the same name.

All affected provinces are preserved, duplicate source claims are deduplicated,
and each state's population totals by all original pop attributes are conserved.
Pops and buildings move to valid owner scopes. Other ownership states retain
their complete original blocks. Existing banners are retained; the three new
tags receive abstract gameplay banners.

## Sources

- [Met: Western Sahel empires](https://www.metmuseum.org/exhibitions/sahel-art-empire-sahara): Mali and Songhay chronology.
- [Smithsonian: Benin art and royal authority](https://www.si.edu/object/benin-art-power-lart-du-benin-instrument-du-pouvoir%3Asiris_sil_543135): Benin's fifteenth-century expansion.
- [Met: Central Africa, 1400–1600](https://www.metmuseum.org/ko/toah/ht/08/afc): Kongo and the later emergence of Luba.
- [Met: Eastern and Southern Africa, 1400–1600](https://www.metmuseum.org/it/toah/ht/08/afa): Swahili towns, Mutapa and Butua/Torwa.
- [UNESCO: Kilwa Kisiwani](https://whc.unesco.org/en/list/144): medieval port, mosque and palace remains.
- [Met: Asante royal staff](https://www.metmuseum.org/art/collection/search/315887): Asante Empire chronology, circa 1700–1900.
- [Getty: Palace Sculptures of Abomey](https://www.getty.edu/conservation/publications_resources/pdf_publications/pdf/palace2.pdf): Dahomey's later formation.
- [Te Ara: Ngāpuhi lands](https://teara.govt.nz/en/ngapuhi/page-1) and [tribal development](https://teara.govt.nz/en/tribal-organisation/page-2): Northland homeland and evolving iwi/hapū identities.

The later regional/Pacific revision is described in `africa_pacific_regions.md`.
Run `tools/audit_africa_nz.py`, `tools/audit_australia.py` and
`tools/audit_north_america.py` for static validation. A fresh game start is
still needed to verify behavior in the Victoria 3 engine.

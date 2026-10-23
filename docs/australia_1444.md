# Australia in 1444

Seven independent playable countries use `country_type = unrecognized`:

| Tag | Name | Territory |
| --- | --- | --- |
| NNG | Noongar | Existing southwest Australian territory |
| KAU | Kaurna | Existing South Australian territory |
| GML | Gamilaraay | Existing New South Wales territory |
| K16 | Kulin | Existing Victorian territory, with Gunditjmara separated |
| Y06 | Yolngu | Existing Arnhem Land territory |
| T19 | Tiwi | Existing Tiwi territory |
| GDT | Gunditjmara | Nine provinces in southwest Victoria |

`AUP`, Aboriginal Australian Peoples, is the sole decentralized owner of all
remaining territory in Australia's seven state regions, including Tasmania.
It is a regional gameplay aggregate, not an assertion of a single historical
people or government. New Zealand, New Guinea and the Pacific are unaffected.
Retired Australian tags remain defined for compatibility but own no Australian
territory at the start. N07 is retained for its use outside Australia.

Centralization and the monarchy/autocracy government defaults are gameplay
choices requested for playability, following the mod's North American setup.
They do not establish that these peoples were centralized monarchies in 1444.
The Kulin grouping is a convenient representation of connected peoples, not a
dated claim that a unified state existed in 1444. The broad original Kulinic
language-family territory in New South Wales joins AUP.

Existing province boundaries are approximate. Gunditjmara provinces were chosen
from the western/southwestern part of the former Victorian Kulinic assignment,
using province centroids from the installed game bitmap. They are not surveyed
traditional boundaries. Remaining playable territories retain the source mod's
footprints. All tags use the existing `aborigine` culture and `animist` religion.
The migration conserves each state's population by every original pop attribute;
split populations use province-count proportions and integer remainder allocation.
Duplicate source province entries are collapsed to one owner. No economic
buildings are added: all Australian source building scopes were empty.
Kaurna retains its existing banner. The other playable tags and AUP receive
abstract gameplay banners, not purported historical flags.

## Historical basis

- [AIATSIS: First Peoples of Australia](https://aiatsis.gov.au/explore/first-peoples-australia): diverse peoples and the limitations of umbrella names.
- [Gunditjmara cultural history, Budj Bim](https://www.budjbim.com.au/about-us/our-culture/): long-lived aquaculture networks, at least 6,600 years old; the strongest archaeological rationale for a distinct Gunditjmara tag.
- [Wurundjeri Woi-wurrung Country Plan](https://www.wurundjeri.com.au/wp-content/uploads/2026/01/Wurundjeri-Woi-wurrung-Whole-of-Country-Plan-2025-2035.pdf): the five connected Kulin peoples in central Victoria.
- [National Museum of Australia: Yolngu](https://www.nma.gov.au/exhibitions/yalangbara/yolngu): eastern Arnhem Land identity and history. Later Macassan contact is not projected back to 1444.
- [Australian Government Aboriginal engagement guide](https://www.facs.nsw.gov.au/__data/assets/pdf_file/0003/322248/working_with_aboriginal_people.pdf): geographic identification of Noongar in southwest Australia and Yolngu in the Top End.

Run `tools/audit_australia.py` with Python to check ownership, conservation,
pop/building scopes, capitals, types, laws and localization against
`docs/australia_1444_baseline.json`. Runtime playability still requires a fresh
1444 campaign in Victoria 3; no game launch is part of this static audit.

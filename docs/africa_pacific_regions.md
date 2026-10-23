# African regions, Pacific islands and Hawaii

The former African Peoples aggregate is partitioned into three decentralized
owners. The 33 selected playable African tags and all other centralized countries
retain their territory.

| Tag | Display name | Scope | Capital state |
| --- | --- | --- | --- |
| AFD | Northern and Western African Peoples | North Africa, West Africa, Nile basin except Equatoria | Guinea |
| AFC | Central African Peoples | Equatorial Africa: Congo basin, Cameroon, Chad, Angola | Equateur |
| AFE | Eastern and Southern African Peoples | East and southern Africa, Madagascar, Equatoria | Zambia |

Assignments follow the installed game's strategic state regions. They apply
only to the previous aggregate's provinces. African owners total 68 instead
of the original 143, with exactly three active decentralized tags.

`OPD`, Pacific Island Peoples, replaces the decentralized owners in Micronesia,
Fiji, Tonga, Vanuatu, Kanak, Bougainville, the Solomon Islands, Nauru and both
halves of New Guinea. The existing centralized Tahiti remains independent.
The established Australian and New Zealand setups are preserved, including
their separate regional decentralized remainders and playable tags.

Hawaii (`HAW`) owns all three provinces in the complete Hawaiian state, verified
against the installed game's state-region definition. It is centralized
(`unrecognized`) and incorporated, with the standard playable startup laws.
Its state religion is animist, replacing the inherited Protestant definition
for the 1444 setup. This unified kingdom is a requested gameplay abstraction.

Pops retain their original cultures, religions, types and sizes. Buildings retain
levels, reserves, production methods and ownership levels. Owner scopes are
updated for the regional tags. Anachronistic minority pops inherited from the
source setup are preserved rather than silently removed. Retired Pacific tags
remain defined without starting territory, and their obsolete diplomatic clauses
are removed. New aggregate flags are abstract gameplay banners.

`tools/audit_africa_pacific.py` checks the exact regional assignments, full Hawaii
ownership, conservation of provinces, population and buildings, valid country
and history data, and unchanged unrelated ownership blocks.
`tools/audit_africa_nz.py` also runs this revision audit when its baseline exists.
In-game validation still requires a fresh campaign.

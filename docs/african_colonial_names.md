# African colonial names

African administrations now have national names for twelve colonial traditions:
Castilian/Spanish, Portuguese, French, English/British, Dutch, Danish, Swedish,
Brandenburg, Prussian, German, Belgian, and Omani. The Dutch rules recognize both
Holland and the Netherlands; Brandenburg uses this mod's BBR tag.

This adds 40 national names across the five existing administration areas and 17
names selected by the colonial capital. Every name has an English adjective.

| Administration variable | Area used by the existing creation buttons |
| --- | --- |
| `cape_verde_subject_var` | Cape Verde |
| `senegal_subject_var` | West Africa, including the Guinea coast and Niger basin |
| `congo_subject_var` | Equatorial Africa, including Angola and Cameroon |
| `southern_africa_subject_var` | Southern Africa |
| `zanj_subject_var` | East Africa, including Mozambique and Madagascar |

The variable names are older than these broad boundaries. A West African
administration is not necessarily Senegal, and an equatorial administration is
not necessarily Angola. Portuguese Congo replaces Angola as the broad Portuguese
equatorial name; Angola applies when its capital is in an Angolan state.
Castilian West Africa uses Governorate of Guinea, with Governorate of Senegambia
available for a Senegal capital.

| Power | More specific capital-based names |
| --- | --- |
| Castile/Spain | Governorate of Senegambia |
| Portugal | Cacheu and Bissau, Angola, Mozambique |
| France | Senegal, French Madagascar |
| England/Britain | Gold Coast, Sierra Leone |
| Netherlands/Holland | Dutch Gold Coast |
| Denmark | Danish Gold Coast |
| Sweden | Swedish Gold Coast |
| Brandenburg | Brandenburg Gold Coast |
| Prussia | Prussian Gold Coast |
| Germany | Togoland, Kamerun, German South West Africa |
| Oman | Zanzibar |

Names describe the seat of the existing regional administration; they do not
create smaller colonial countries. Moving the capital can therefore change the
name. There are no date gates: historical names are available when an alternate
campaign reaches the corresponding place earlier.

National names have priority 200 and capital-based names priority 220, above the
existing generic regional names at 100. Each rule checks the administration
variable and current direct overlord. A transferred colony takes its new
overlord's name; independence disables these national rules and leaves the
existing fallback naming behavior in charge. New rules stay inside the existing
`DEFAULT` block because another block would replace it rather than extend it.

Historical names supply the regional vocabulary. Unattested combinations use
restrained geographic alternatives such as Danish East Africa, Dutch Congo,
and Omani Cape. These are alternate-history names, not claims that those
colonies existed. Administrative titles avoid assuming a particular monarch,
dynasty, or republican constitution.

Historical references used for the naming choices:

- [Danish National Museum: Danish colonies](https://en.natmus.dk/historical-knowledge/historical-themes/danish-colonies/?force=desktop) — Danish Gold Coast.
- [Dutch National Archives: Ghana](https://www.nationaalarchief.nl/onderzoeken/zoekhulpen/ghana) — Dutch forts on the Gold Coast and Guinea coast terminology.
- [Living History Forum: historical research into racism in Sweden](https://www.levandehistoria.se/sites/default/files/material_file/historical_research_into_racism_and_racial_intolerance_in_sweden.pdf) — Swedish Gold Coast.
- [Prussian Palaces and Gardens Foundation: Brandenburg's West African venture](https://www.spsg.de/en/research-collections/research/colonial-contexts-in-the-prussian-palaces-and-gardens-foundation-berlin-brandenburg-spsg/medallion-for-the-start-of-brandenburgs-seafaring-venture-to-the-coast-of-west-africa-in-1681) — Brandenburg's Gold Coast settlements.
- [National Army Museum: West Africa campaign](https://www.nam.ac.uk/explore/west-africa-campaign) — Togoland and Kamerun.
- [Portuguese Heritage Information System: Cacheu](https://hpip.org/en/Contents/Place/225) — Portuguese Guinea trading settlements.

Validation: `node tools/audit_colonial_names.cjs` checks localization, country
tags, state references, naming priority, current overlord selection, and
independence. Pass an installed game directory as the first argument if needed.
The audit is static; map labels still need visual verification in a running game.

The same powers now also have [American and Australasian names](american_australasian_colonial_names.md).

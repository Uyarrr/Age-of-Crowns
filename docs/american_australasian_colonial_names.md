# American and Australasian colonial names

This extends the African naming pass to the same twelve national traditions.
The Americas already had Castilian/Spanish, Portuguese, French, and
English/British names. Dutch, Danish, Swedish, Brandenburg, Prussian, German,
Belgian, and Omani names now cover all nine existing American administration
areas: Canada, Atlantic Coast, Pacific Coast, Great Plains, Central America,
Gran Colombia, Andes, La Plata, and Brazil.

The addition contains 113 rules and their English adjectives:

- 72 national American names for the eight previously missing powers.
- 24 national names for Australia and New Zealand, covering all twelve powers.
- 12 Caribbean names, selected when a Central American administration has an island capital.
- New Holland for Dutch Brazil with a capital in Pernambuco, Paraíba, or Rio Grande do Norte.
- Van Diemen's Land for English/British or Dutch Australian colonies with a Tasmanian capital.
- Two generic Australian and New Zealand fallbacks for other colonial powers.

## Naming choices

New Netherland and New Sweden supply historical names for Dutch and Swedish
Atlantic colonies. Dutch northeastern Brazil and Dutch Australia can both be
called New Holland: the duplicate reflects historical usage in different places.
The Dutch New Zealand name is Nieuw Zeeland.

Alternate colonial names use familiar naming patterns, such as New Friesland,
New Jutland, New Brandenburg, New Prussia, New Brabant, and New Flanders. Other
holdings use geographic forms such as Swedish California, Danish Peru, Belgian
La Plata, or Omani Brazil. These are plausible alternatives, not assertions that
those colonies existed. There are no invented dynasties, monarch-specific
dedications, or constitution-dependent titles.

| Power | Australia | New Zealand |
| --- | --- | --- |
| Castile/Spain | Tierra Austral | Nueva Zelanda |
| Portugal | Terra Austral | Nova Zelândia |
| France | Terre Australe | Nouvelle-Zélande |
| England/Britain | Australia | New Zealand |
| Netherlands/Holland | New Holland | Nieuw Zeeland |
| Denmark | Danish Australia | Ny Zeeland |
| Sweden | Swedish Australia | Nya Zeeland |
| Brandenburg | Brandenburg Australia | Brandenburg New Zealand |
| Prussia | Prussian Australia | Prussian New Zealand |
| Germany | German Australia | German New Zealand |
| Belgium | Belgian Australia | Belgian New Zealand |
| Oman | Omani Australia | Omani New Zealand |

The three Romance Australian names adapt the traditional southern-land
terminology. They are alternate colonial names here, rather than claims of
historical Spanish, Portuguese, or French settlement governments.

## Integration

American national names require the existing administration variable and the
current direct overlord. Caribbean rules use the existing island geography,
so a Cuba-based administration can receive Spanish West Indies instead of
the mainland Captaincy General of Guatemala name. The twelve Caribbean names
use each power's national label; the English/British rule shares British West
Indies in keeping with the existing shared English/British naming tradition.

Australia and New Zealand do not have the American administration variables.
Their rules use the capital's existing geographic region and
`aoc_is_or_was_colonial_nation`, which recognizes colonial country type, colony
subject status, or the permanent colonial initialization marker. This supports
both fixed tags such as AST/NZL and generated colonial countries. Ordinary local
protectorates without colonial status or the marker retain their names.

National rules require a current direct overlord and have priority 200.
Caribbean, northeastern Brazilian, and Tasmanian seat names have priority 220.
Moving the capital can change a seat name; it does not create a new country or
change administration boundaries. Generic Australian/New Zealand names have
priority 100 and use the engine's overlord prefix. Independence turns off the
national rules and leaves the regional fallback available for colonial countries.
Existing American creation mechanics and regional boundaries are unchanged.

All rules remain in the single existing `DEFAULT` block. A second block would
replace the existing default database rather than extend it.

Historical references:

- [US National Park Service: New Netherland](https://www.nps.gov/mava/learn/historyculture/new-netherland.htm) — New Netherland and New Sweden.
- [National Library of Australia: the name Australia](https://www.library.gov.au/research/research-guides-0/where-name-australia-came) — New Holland and southern-land terminology.
- [National Museum of Australia: Tasmania](https://www.nma.gov.au/defining-moments/resources/separation-of-tasmania) — Van Diemen's Land.

Run `node tools/audit_colonial_names.cjs` to validate all four continental naming
groups. The static audit covers localization, country tags, state references,
overlord changes, priority conflicts, independence, colonial identity, and
Caribbean/Australasian geographic selection. Visual verification in a running
game remains outstanding.

# Siberian Frontiers

Siberian Colonization is a state trait that requires `siberian_frontiers` to begin colonization. The same technology disables the trait. It imposes no growth or mortality penalty after research. Siberian Frontiers is available to every country in Age 5 Society, with Colonization and Absolutism as prerequisites. Muscovy and Russia receive higher AI research priority.

The trait covers Tomsk, Tobolsk, Upper Yeniseysk, Ob, Kamchatka, Okhotsk, Yakutsk, Trans-Baikal, Irkutsk, Surgut, Krasnoyarsk, Altai, Buryatia, Kolyma, and Amur. Existing Siberian terrain modifiers remain separate. This controls colonial expansion, not conquest or existing ownership.

All 76 malaria/severe-malaria assignments are removed from the installed 1.15 map. Neutral replacement definitions prevent inherited malaria traits from imposing penalties. Unused Quinine and Malaria Prevention localization is removed. Other colonization laws, range, and growth rules remain in effect.

Five map files override the installed game files: `03_north_africa.txt`, `04_subsaharan_africa.txt`, `12_indonesia.txt`, `14_siberia.txt`, and `15_russia.txt`. Review these overrides when updating to a new map version. Use a new campaign to load the changed map traits; existing saves retain their saved traits.

## Artwork

Generated with the built-in imagegen tool. The local reference PNGs were extracted from the mod's Colonization and New World DDS icons and the installed game's Malaria DDS icon. Source PNGs preserve the full generated resolution and alpha. Runtime assets are DXT5 DDS with alpha, 150 × 150 for the state trait and 256 × 256 for the invention.

- `gfx/interface/icons/state_trait_icons/siberian_colonization.dds`
- `gfx/interface/icons/invention_icons/siberian_frontiers.dds`

### State trait prompt

Use case: stylized-concept. Generate one game state-trait icon for Siberian Colonization, matching the reference malaria icon visible in the conversation: circular bronze/copper medallion, thin pale ivory and dark metallic rim, warm amber shaded interior, simple nearly black silhouette, clean readable at 150x150. Replace mosquito subject with a snow-laden Siberian fir tree and a small wooden frontier palisade silhouette in front, with a subtle snowbank silhouette. Centered single round medallion occupying 92% of square canvas. Outside the medallion genuinely transparent. No lettering, no text, no numbers, no watermark. Keep restrained warm brown palette and original malaria medallion style, not a detailed painting.

### Invention prompt

Use case: historical-scene. Asset: a single square invention/technology icon named Siberian Frontiers for a historical grand strategy mod. Match the two existing colony invention icons visible in the conversation: isolated compact arrangement of finely illustrated objects, realistic hand-painted collectible game-item art, crisp engraved details, muted parchment tan, aged brown wood and steel, gentle upper-left highlights, soft dark edge shading, transparent background. Main composition: fur-lined seventeenth-century Russian explorer cap with brown fur and dark red cloth, resting beside a rolled parchment route map with NO legible writing, a brass compass, an axe and bundle of sable pelts; behind objects a small timber palisade watchtower and snow-dusted Siberian evergreen to communicate frontier settlement. Keep a strong simple silhouette and focus on fur cap, compass, map, and timber tower, with secondary objects subordinate, readable when downscaled to 256x256. Entire object grouping within canvas with small transparent margin, no circular badge, no border, no backdrop, no people, no modern items, no text or labels or watermark. Real alpha outside objects. Not photoreal photography, not cartoon; match the polished detailed hand-painted icon art of existing colonization/new_world references.

## Validation

Run `node tools/audit_siberian_frontiers.cjs` and `node tools/audit_map_ownership.cjs`. The first verifies map equivalence apart from the intended traits, complete malaria removal, exact frontier coverage, technology prerequisites and era, localization, and DDS dimensions. The second checks province ownership integrity. In-game behavior and rendering still require a game launch.

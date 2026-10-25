# Iron Mine Distribution Research

## Scope and balance

- Previous map: 303 iron-bearing states and 4,075 total mine levels.
- Rebuilt map: 265 iron-bearing states and 4,004 total mine levels.
- The 1.7% reduction in world capacity is intentionally small. The change is geographic, not a global iron nerf.
- Every mine cap has a matching `resource` block with the same `undiscovered_amount`.

Mine levels are a gameplay abstraction of economically exploitable ore, deposit scale, grade, accessibility, historical importance, and regional competition. They are not a direct conversion of reserve tonnage.

## Tier rules

| Levels | Role | Examples |
| ---: | --- | --- |
| 45-60 | World-class province | Pilbara, Carajas, Mesabi, Kursk, Kryvyi Rih, Norrbotten, Northern Cape |
| 26-44 | Major mining belt | Labrador Trough, Mauritania, Simandou, Transvaal, Urals, Kerman, Bayan Obo |
| 13-25 | Important regional district | Asturias, Upper Silesia, Bosnia, Erzurum, Hubei, Tohoku |
| 7-12 | Local or historically useful field | Smaller European, Andean, African, and Asian workings |

## Geographic anchors

- Australia: Western Australia carries the Pilbara/Hamersley system; South Australia represents the Middleback Ranges and large magnetite resources.
- Brazil: Para represents Carajas; Minas Gerais represents the Quadrilatero Ferrifero. Secondary caps cover Bahia, Mato Grosso, and Goias.
- North America: Minnesota and Michigan represent the Lake Superior ranges. Quebec and Newfoundland share the Labrador Trough. Alabama and Utah retain smaller historical fields.
- South America: Bolivar represents the Venezuelan Guiana Shield deposits; Ica and Arequipa cover Peru's principal coastal iron belt; northern Chile retains magnetite districts.
- Europe: Norrland represents Kiruna-Malmberget; Lorraine, the Basque Country, Asturias, Upper Silesia, Styria, Bosnia, Wales, Yorkshire, and the Midlands retain historically important industrial ore.
- Russia and Ukraine: Kursk represents the Kursk Magnetic Anomaly; Cherson is the map's closest state container for Kryvyi Rih; the Urals, Chelyabinsk, Kola, Akmolinsk, and Aktobe carry the other major belts.
- India: Orissa, Central Provinces, Bihar, and Mysore represent Odisha, Chhattisgarh/Madhya Pradesh, Jharkhand-Singhbhum, and Karnataka.
- China and Korea: Shengjing represents Anshan/Liaoning; Alxa represents the Bayan Obo/Inner Mongolian belt; southern Manchuria, Zhili, Sichuan, Hubei, Shandong, and Pyongyang retain major regional fields.
- Africa: Mauritania, Simandou in Guinea, Liberia-Sierra Leone, Belinga in Gabon, Mbalam in Cameroon, Transvaal, and Northern Cape form the principal high-capacity arc.
- Middle East: Kerman, Isfahan, Khorasan, and Semnan carry Iran's major iron provinces; Anatolian deposits are concentrated in Ankara, Erzurum, and Adana.

## Method

1. Locate documented ore districts in the closest available state-region container.
2. Rank deposits by geological scale and grade, then adjust for transport, historical exploitation, and the mod's state granularity.
3. Preserve industrial-era districts even when modern output is low, but avoid giving every reported occurrence a mine cap.
4. Keep the global total close to the previous map so prices and construction demand do not change solely because of the remap.
5. Concentrate capacity enough to create meaningful mining regions and trade, while retaining regional sources for gameplay resilience.

## Principal sources

- U.S. Geological Survey, [Iron Ore Statistics and Information](https://www.usgs.gov/centers/national-minerals-information-center/iron-ore-statistics-and-information).
- U.S. Geological Survey, [Mineral Commodity Summaries 2025](https://pubs.usgs.gov/periodicals/mcs2025/mcs2025.pdf), pp. 99-100.
- Geoscience Australia, Australian mineral-resource reporting for iron ore and the Pilbara/Hamersley province.
- Natural Resources Canada, iron ore facts and Labrador Trough production geography.
- Indian Bureau of Mines, Indian Minerals Yearbook: Iron Ore, with state-level resource and production tables.
- Agencia Nacional de Mineracao and Servico Geologico do Brasil, Brazilian mineral yearbooks and Carajas/Quadrilatero Ferrifero geology.
- LKAB, Kiruna, Malmberget, and Svappavaara operating and resource material.
- Troll et al. (2019), [Global Fe-O isotope correlation reveals magmatic origin of Kiruna-type apatite-iron-oxide ores](https://doi.org/10.1038/s41467-019-09244-4).
- Rio Tinto Guinea, [Simandou project](https://riotintoguinee.com/en/simandou-project/).

Research and map rebuild completed 2026-06-15.

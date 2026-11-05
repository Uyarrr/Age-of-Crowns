# English and British overseas journals

Content lives in `england_overseas` files under the relevant `common/` folders,
`events/england_overseas_events.txt`, and the BOM-encoded English localization file
`localization/english/england_overseas_l_english.yml`.

The six journals have distinct crowned heraldic DDS icons, also used by their
events and rewards. See [the art manifest](england_overseas_art/README.md) for
sources, prompts, conversion details, and the preview sheet.

Available to independent, non-revolutionary England and Great Britain. Colonization technology is required for charter buttons.
Creation and territory transfers require peace and no committed diplomatic play.
They transfer only directly owned territory; they never take foreign land.

## Progression and balance

| Journal | Requirements | Reward, always 25 years |
| --- | --- | --- |
| The Cape of Good Hope: first milestone | Subject SAF holds Cape land, 25,000 population, £100,000 GDP, a port | +10% convoy capacity, +2 declared interests; declares interests in northern and southern India and unlocks the Indian journal |
| The Cape of Good Hope: completion | SAF owns the entire Cape state, 150,000 population, £750,000 GDP, at least 25% GDP growth from the first assessment, SoL 10 | +15% convoys, +5% construction, +10% prestige |
| The East India Company | Chartered subject BIC has possessions in three distinct Indian state regions, 250,000 population, £500,000 GDP | +5 percentage points company throughput bonus, +10% textile throughput, +15% convoys; unlocks Australasia |
| Australia and New Zealand | Crown and subjects own 50% of Australian provinces and 50% of New Zealand provinces; AST has 300,000 population/£1.5m GDP/SoL 10; NZL has 80,000/£400,000/SoL 10 | Crown: +15% migration attraction and convoys, +10% agriculture throughput. AST and NZL each: +25% attraction, +15% construction, +10% agriculture throughput |
| The Hudson's Bay Company | Chartered HBC has land in three interior state regions, 100,000 population, £400,000 GDP, a hunting lodge with at least five levels and 50% employment; Crown owns its unique company | +20% hunting-lodge throughput, +5 percentage points company throughput bonus, +10% prestige |
| Expand the Royal Navy | Top three naval power projection and naval-supplies production, with a shipyard at least 50% employed, for 120 consecutive monthly assessments | +15% naval offense and defense, -20% convoy damage, +15% military-industry throughput, +25% prestige from naval power |
| Dominate the New World | Complete Hudson's Bay and navy journals; land in 35 American state regions, including 8 North American and 6 Central American; four direct colonial/company subjects with American land; combined American population 5m/GDP £20m; ten American states with qualifying production buildings at least level five and 75% employed | +25% prestige and convoys, +15% construction, bureaucracy and manufacturing throughput, +20% plantation throughput |

All six entries are listed in England’s and Great Britain’s start-map journal
preview, including later entries whose progression requirements are not yet met.
Country eligibility is checked by visibility, rather than repeated in the visible
activation checklist. Dynamic status text uses the journal’s country and falls
back to static text until its progress variables have been initialized.

Monthly assessments update regional totals. Australian coverage includes Tasmania;
New Zealand includes both islands. Coverage counts owned provinces against the
whole region's province count, including independently held territory. Split states
cannot inflate either coverage or the Indian/Canadian distinct-region requirements.
American economic totals exclude possessions outside the Americas, even when a
subject has land on multiple continents. Subject-of-subject land counts toward
Crown territory; the four colonial administrations must be direct subjects.

The Cape growth target is recorded once on establishment or first assessment of
an existing subject. The first Cape milestone does not finish its journal. Naval
progress resets to zero whenever either ranking or the shipyard check fails.
Country completion flags prevent repeated rewards, including after tag formation.

## Charters and companies

The five charter buttons create the existing historical tags **at runtime**:
SAF (Cape), BIC (India), AST (Australia), NZL (New Zealand), and HBC. `AUS` is
Austria and is deliberately not used. Fixed tags preserve existing country,
flag, and formation content; no duplicate anonymous dynamic country is generated.
An existing foreign-held tag blocks the charter. Existing qualifying subjects can
be endowed and linked to their company. Further button uses transfer newly owned
regional land without granting the founding buildings again. Endowments are also
tracked on the sponsor so annexing and re-creating a subject cannot farm buildings.

BIC and HBC are chartered-company subjects of the sponsor. Separate unique company
types belong to the English/British sponsor, link to their territorial country with
the vanilla `add_owned_country` effect, and own the initial colonial textile mills
or hunting lodges. This follows vanilla Britain's company/country ownership model.
Their prestige goods are Company Calicoes (`clothes`) and Hudson's Bay Beaver
Pelts (`fur`), using existing art and the normal company prestige-goods mechanics.

Initial endowments: Cape two ranch levels; BIC two company-owned textile levels
and two cotton plantation levels; AST two ranch levels; NZL two logging levels;
HBC three company-owned hunting-lodge levels. Coastal possessions receive a basic
port. Population is developed through normal gameplay rather than fabricated pops.
BIC receives claims to Gujarat, Bombay, Madras, Circars, and East and West Bengal;
these are claims, not automatic transfers of Indian rulers' territory.

Hudson's Bay is removed from Canada's provincial journal and its old scripted
button is removed. Canada's description is revised accordingly. Generic southern
African administrations exclude the Cape state for England/Britain so that those
buttons cannot consume the dedicated Cape foothold. Other southern African states
remain available to the generic administration system. Two higher-priority display
names are added inside the existing BIC and SAF name definitions.

## Historical approach

This is a 1444-start alternate-history progression, so historical dates provide
context rather than hard unlock years. The Cape-to-India-to-Australasia sequence
is a gameplay structure rather than a claim that Britain founded these colonies
in that order. The combined Australian administration is a gameplay abstraction;
New Zealand receives its own government. The Canadian interior includes later
Hudson's Bay expansion and does not reproduce the 1670 drainage-basin boundary.
Descriptions acknowledge Indian political authority and Indigenous trading partners
and inhabitants rather than treating already populated territories as empty land.

Historical references consulted:

- [National Army Museum: Armies of the East India Company](https://www.nam.ac.uk/explore/armies-east-india-company), the 1600 foundation and evolution from trading settlements to territorial military power.
- [Science Museum Group: East India Company](https://collection.sciencemuseumgroup.org.uk/people/ap24606/east-india-company), the 1600 royal charter and trade in textiles and tea.
- [Canadian Commissioner of Official Languages: Hudson's Bay Company](https://www.clo-ocol.gc.ca/en/founding-hudsons-bay-company-which-secures-monopoly-fur-trade-hudson-bay-region-english-crown), the 1670 charter, trading posts, and Indigenous trade relations.
- [NZ History: New Zealand becomes a British colony](https://nzhistory.govt.nz/letters-patent-issued-making-new-zealand-a-colony-separate-from-new-south-wales), the separate colonial charter and connection to New South Wales.
- [South African Government: South African Yearbook, History](https://www.gov.za/sites/default/files/gcis_document/202602/south-african-yearbook.pdf), British occupations in 1795 and 1806 and the strategic Cape route.

## Verification

Run `node tools/audit_england_overseas.cjs`. The audit parses Clausewitz blocks,
checks content references against the mod and installed vanilla data, validates
English localization and reward durations, and checks key progression safeguards.
This is static validation, not an engine playtest.

In-game checks still required: start as ENG, trigger both Cape milestones, charter
BIC from a coastal foothold and acquire three separate regions, form AST and NZL,
verify the regional ownership counters, charter HBC and inspect its parent company
and prestige-good eligibility, break the naval rankings after 119 months to verify
reset, then complete the Atlantic capstone. Also repeat a charter after acquiring
more land, test a foreign-owned historical tag, and form GBR midway through the
chain. Check the Victoria 3 error log after loading and after each charter.

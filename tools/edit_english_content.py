"""Apply the reviewed English copy. Safe to run repeatedly."""
from pathlib import Path
import re

def edit(name, fn):
    p = Path(__file__).resolve().parents[1] / name
    old = p.read_bytes()
    text = old.decode('utf-8-sig').replace('\r\n', '\n')
    result = fn(text)
    if old.count(b'\r\n') > old.count(b'\n') / 2:
        result = result.replace('\n', '\r\n')
    p.write_bytes((b'\xef\xbb\xbf' if old.startswith(b'\xef\xbb\xbf') else b'') + result.encode())

COPY = {
 'form_deseret_dec_desc': 'Unite our communities under a common constitution. A government in Deseret would protect religious life, maintain public order, and give our settlements a lasting political home.',
 'opium_wars.2.f': 'The merchants point to their ledgers: demand remains high, and prohibition would surrender a profitable trade to their rivals. The costs borne by the consumers do not appear in the accounts.',
 'opium_wars.8.f': 'The pipe lies within reach. Beyond the bed, voices call and work goes unfinished; the will to rise returns long before the strength.',
 'communist_elections.1.f': 'First they take the great estates, the speaker warns. Then the smaller houses. By the time the listeners begin to object, there will be no one left to hear them.',
 'crime_events.11.f': 'The inspector watches the prisoner eat in silence. The familiar face is difficult to reconcile with the reports stacked upon the desk. Outside, the press is already gathering.',
 'expedition_events.620.f': 'The channel narrows between rocks and drifting timber. A sudden crack breaks the quiet: the hull has struck an obstacle below the waterline.',
 'ig_suppression_events.4.f': 'The agent returns with an untroubled expression. Persuasion has failed, but the prisons still have room.',
 'expedition_events.294.f': 'Another settlement appears beside the river. We prepare needles, mirrors, and ribbons for exchange. Beyond this point, our charts will be less useful than the advice of those who live here.',
 'expedition_events.120.f2': 'A villager leads us to [SCOPE.sCharacter(\'old_expedition_leader\').GetFullName]. Illness and isolation have taken their toll. Recognition comes slowly, followed by a cry that brings the whole expedition running.',
 'expedition_events.130.f': 'The traders greet us readily. Then a captive pushes forward, identifies himself as the [SCOPE.sC(\'ambassador_country\').GetAdjectiveNoFormatting] ambassador, and begs us to intervene.',
 'exhibition_events.7.f': 'The attendant offers a view through the telescope for one penny. The instrument gleams beneath the exhibition lamps. Admission has already emptied most of the visitor’s purse.',
 'suffragist_events.10.f': 'After years of meetings, marches, and arrests, the ballot slips quietly into the box. The official moves on to the next voter. An ordinary act has become possible at last.',
 'suffragist_events.1.f': 'The young critic dismisses the marchers as children playing at politics. A passing demonstrator stops and looks directly at the group. The explanation trails off.',
 'africa_colonial_events.6.f': 'The visitor interrupts the interview, distressed by the violence being described. The interpreter listens to the reply, then translates: the community had known little of such conduct before the visitor’s countrymen arrived.',
 'slave_owner_paranoia_events.3.f': 'The planter insists that even a moderate abolitionist is dangerous. Every public criticism of slavery, the argument runs, gives the enslaved another reason to hope that it can end.',
 'red_scare.2.f': 'The refugee describes a supposed Ministry of Free Love and compulsory marriages. Each question produces a more lurid detail. The reporter pauses over the notebook, uncertain how any of it could be verified.',
 'je_england_1_reason': 'The Crown still claims the throne of France. Hold land in eight French state regions, directly or through subjects, to secure the claim. The loss of all but two regions ends our continental ambitions.',
 'je_england_2_reason': 'Lancaster holds the throne; York challenges its rule. Noble patronage shifts the succession, while weak government raises Realm Tension. At 60 Tension, a rival house can form a revolutionary movement.\n\nSecure your dynasty after war through 24 consecutive months of low tension and firm support. Lancaster can also avert war through 36 months of peaceful government. The requirements below track a lasting settlement.',
 'je_england_3_reason': 'Rival crowns and lordships divide the British Isles. Bring every state in Britain and Ireland under direct rule to secure a united realm.',
 'je_england_colonization_of_canada_reason': 'Give our Canadian possessions permanent governments. Charter the five regional colonies as land is acquired. Newfoundland remains under direct rule; the inland fur trade belongs to the separate Hudson’s Bay charter.',
 'wotr_final_settlement_tt': 'Secure a dynastic settlement:\n• After war: #v [ROOT.GetCountry.MakeScope.Var(\'wotr_stability_months_var\').GetValue|0]#!/24 consecutive months at Tension ≤30, with no revolution. Lancaster needs Succession ≥65; York needs ≤35.\n• Without war: #v [ROOT.GetCountry.MakeScope.Var(\'wotr_peaceful_months_var\').GetValue|0]#!/36 months at Tension ≤20 and Succession ≥65, after the Royal Crisis begins.\nA Tudor victory ends the crisis immediately.',
 'wotr_phase_one_begins_tt': '#title Phase I: The Uneasy Realm#!\nMonthly phase effect: #g −0.15#! Tension. The Royal Crisis begins with $renaissance$ or Tension of 55.',
 'wotr_phase_two_begins_tt': '#title Phase II: The Royal Crisis#!\nMonthly phase effect: #r +0.20#! Tension. At 50 Tension, York demands a protectorate.',
 'wotr_phase_three_begins_tt': '#title Phase III: Open Conflict#!\nMonthly phase effect: #r +0.40#! Tension. Rival dynastic movements can form at 60 Tension.',
 'wotr_summon_great_council_button': 'Summon the Great Council',
 'wotr_summon_great_council_button_desc': 'Seek a settlement with the magnates. The council costs £1,000 per week for three years. Another cannot be summoned for four years.',
 'wotr_summon_great_council_button_effect_tt': 'Eases the monthly rise in Realm Tension and grants #v $war_of_the_roses_great_council$#! for #v 3 years#!. Another council can be summoned after #v 4 years#!.',
 'wotr_favor_lancaster_button_desc': 'Reward Lancastrian supporters. Patronage strengthens their claim but raises Realm Tension. Neither faction can receive another grant for three years.',
 'wotr_favor_york_button_desc': 'Grant offices to Yorkist supporters. Patronage strengthens their claim but raises Realm Tension. Neither faction can receive another grant for three years.',
 'england_hyw_victory.desc': 'English rule and loyal subjects now extend across much of France. The Crown’s old claim has become a credible bid for the French throne.',
 'england_hyw_victory.flavor': 'Across the Channel, heralds proclaim the same king in two languages.',
 'england_hyw_defeat.desc': 'Our French possessions have dwindled beyond recovery. Defeat leaves the Crown burdened by debt and the magnates questioning its judgement.',
 'england_hyw_defeat.flavor': 'The soldiers return with arrears of pay. The men who sent them have fewer answers.',
 'england_hyw_victory.a': 'Our claim stands vindicated.',
 'england_hyw_defeat.a': 'We must rebuild at home.',
 'england_new_world_canada.desc': 'Atlantic fishermen report sheltered harbours and a great river leading inland. Merchants seek royal backing for permanent settlements in Canada.',
 'england_new_world_canada.flavor': 'A fishing station needs a season’s supplies. A colony needs years of credit.',
 'england_new_world_canada.a': 'Back the Canadian venture.',
 'england_new_world_canada.b': 'Keep our resources at home.',
 'england_the_justices_of_peace.desc': 'Justices of the Peace enforce royal law in the shires. Strengthening their office would improve local government and weaken the magnates’ influence.',
 'england_the_justices_of_peace.flavor': 'The petition bears a familiar complaint: the lord’s men have broken the peace, and the lord’s court has found no fault.',
 'england_the_justices_of_peace.a': 'Strengthen the justices.',
 'england_the_justices_of_peace.b': 'Leave local justice to the lords.',
 'england_the_justices_of_peace_a': 'Royal Justices',
 'england_the_justices_of_peace_b': 'Magnates’ Justice',
 'england_the_yorkist_tradition.desc': 'Yorkist councillors favour trained lawyers and clerks for royal office. The nobility objects to seeing its privileges pass to men of humbler birth.',
 'england_the_yorkist_tradition.flavor': 'A pedigree may secure an audience. It cannot balance the accounts.',
 'england_the_yorkist_tradition.a': 'Appoint men of learning.',
 'england_the_yorkist_tradition.b': 'Reserve office for the nobility.',
 'england_war_of_the_roses_start.desc': 'The Lancastrian court holds the Crown, but the House of York gathers allies against its government. Each disputed appointment gives the great lords another reason to take sides.',
 'england_war_of_the_roses_start.flavor': 'At Westminster, retainers wait outside while their masters count the men within.',
 'england_war_of_the_roses_start.a': 'Keep the king’s peace.',
 'england_war_of_the_roses_wakefield.flavor': 'From Sandal Castle, the duke can see his enemies gathering. His councillors urge caution.',
 'england_war_of_the_roses_wakefield.a': 'York must take the field, whatever the risk.',
 'england_war_of_the_roses_princes.desc': 'The Yorkist succession is in dispute. Gloucester seeks the protectorate and the Crown; protecting Edward’s sons would preserve their inheritance but leave their rivals at court.',
 'england_inns_of_court.desc': 'The Inns of Court train lawyers for royal service. Their graduates offer the Crown capable officials, though the magnates resent their growing influence.',
 'england_inns_of_court.flavor': 'In the counting house and the county court, a trained clerk can make the king’s authority felt far from London.',
 'england_inns_of_court.yes': 'Support the Inns.',
 'england_inns_of_court.no': 'Preserve noble appointments.',
 'england_new_world_atlantic_coast.desc': 'Our northern foothold can supply settlements farther down the Atlantic coast. Merchants petition for ships, credit, and permission to establish new colonies.',
 'england_new_world_atlantic_coast.flavor': 'The charts mark harbours. They say little of the peoples who control the routes inland.',
 'england_new_world_atlantic_coast.a': 'Finance the coastal settlements.',
 'england_the_enclosure_movement.desc': 'Landowners seek to enclose common fields and expand commercial farming. Greater estate revenues would come at the expense of villagers who depend on common rights.',
 'england_the_enclosure_movement.flavor': 'The new hedge follows a surveyor’s line across a path the village has used for generations.',
 'england_the_enclosure_movement.a': 'Permit further enclosure.',
 'england_the_enclosure_movement.b': 'Protect the commons.',
 'order_of_chivalry.desc': 'A royal order would reward distinguished service and bind leading nobles to the sovereign. Its supporters seek the Crown’s patronage.',
 'order_of_chivalry.flavor': 'The badge is small enough to pin upon a cloak. The honour brings its wearer close to the throne.',
 'order_of_chivalry.a': 'Found the order.',
 'order_of_chivalry.b': 'The treasury has other duties.',
 'je_aoc_england_cape_reason': 'A settlement at the Cape can provision fleets bound for India. Establish a working port, then develop the colony’s farms, population, and revenues.',
 'je_aoc_england_east_india_reason': 'A royal charter can turn our Indian footholds into a lasting trading enterprise. Establish the Company and secure three productive possessions.',
 'je_aoc_england_australasia_reason': 'Our eastern stations open the southern oceans to settlement. Establish separate governments in Australia and New Zealand, then develop their economies. Indigenous peoples already command the lands and routes our settlers seek.',
 'je_aoc_england_hudson_bay_reason': 'A chartered company can maintain trading posts along the routes into Hudson’s Bay. Its fur trade will depend on Indigenous trappers, reliable supplies, and access to European markets.',
 'je_aoc_england_royal_navy_reason': 'Our overseas possessions depend on secure sea lanes. Keep the fleet and naval-supplies industry among the world’s three strongest for ten consecutive years.',
 'je_aoc_england_new_world_reason': 'A lasting Atlantic empire needs populous colonies, productive farms and workshops, and several regional governments. Build the territory and economy to sustain that ambition.',
 'england_overseas.1.f': 'The harbour’s first promise is modest: water, provisions, and repairs for the next ship east.',
 'england_overseas.2.f': 'Farms supply the anchorage, workshops serve the fleets, and the governor can at last report revenues to match his obligations.',
 'england_overseas.3.f': 'Behind the directors’ accounts lie agreements with Indian rulers, local merchants, and the workers who keep the factories supplied.',
 'england_overseas.4.f': 'The governors’ dispatches now concern harvests, revenues, and disputes over land. Distance has not diminished the demands of government.',
 'england_overseas.5.f': 'The pelts reach the coastal forts by routes known to the Company’s Indigenous trading partners. Without them, the charter would earn little.',
 'england_overseas.6.f': 'A decade’s accounts record timber, cordage, wages, and repairs. At sea, those expenses have become dependable ships.',
 'england_overseas.7.f': 'Cargoes cross the Atlantic under many colonial seals. Their combined value now carries weight in every European counting house.',
 'je_colonial_administration_reason': 'Place regional possessions under a colonial government. It can receive our other holdings in the region and expand into neighbouring decentralized territory under its colonial laws.',
 'colonial_administration_events.1.d': 'We must choose how [SCOPE.sCountry(\'newly_formed_colonial_nation_scope\').GetName] will be governed.',
 'colonial_administration_events.1.f': 'The charter settles who will govern. The laws will decide whose interests that government serves.',
 'colonial_administration_events.1.a': 'Grant a commercial charter.',
 'colonial_administration_events.1.b': 'Support the religious missions.',
 'colonial_administration_events.1.c': 'Build a settler administration.',
 'colonial_administration_events.1.e': 'Organize the colony for extraction.',
 'colonial_administration_events.2.d': 'The break with the metropole has left our government short of funds and personnel. Protests are spreading beyond the reach of the colonial forces.',
 'colonial_administration_events.2.f': 'The orders still bear the old seal. No ships arrive to enforce them.',
 'colonial_administration_events.2.a': 'We must govern with what we have.',
 'national_colonization.1.d': 'Navigators propose a western route across the Atlantic. Secure Caribbean harbours to supply further voyages before attempting a mainland expedition.',
 'national_colonization.2.d': 'Our mariners are extending their voyages along Africa’s Atlantic coast. Trading stations and secure anchorages could support a route around the continent.',
 'national_colonization.3.d': 'Our navigators and merchants can now support a northern expedition. The Saint Lawrence may offer a passage inland and a base for French settlement.',
 'national_colonization.3.t': 'Into the Saint Lawrence',
 'national_colonization.7.f': 'Knowledge of Atlantic winds makes a western crossing possible.',
 'adopt_local_culture_decision_desc': 'Adopt the dominant culture of your capital as your primary culture. This changes cultural acceptance throughout the country.',
}

def rewrite(t):
    def row(m):
        key = m[2]
        value = COPY.get(key)
        return m[0] if value is None else f'{m[1]}{key}: "{value.replace(chr(10), r"\n")}"'
    return re.sub(r'(?m)^(\s*)([^#\s:]+):\d*\s+".*"[ \t]*(?:#.*)?$', row, t)

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    for p in (root/'localization/english').rglob('*.yml'):
        text = p.read_text(encoding='utf-8-sig')
        if any(re.search(r'(?m)^\s*'+re.escape(k)+r':', text) for k in COPY):
            edit(str(p.relative_to(root)), rewrite)
    p = root/'localization/english/england_journal_l_english.yml'
    if 'wotr_council_available_tt:' not in p.read_text(encoding='utf-8-sig'):
        edit(str(p.relative_to(root)), lambda t: t+'\n wotr_council_available_tt: "No Great Council is active, and four years have passed since the last summons"\n')

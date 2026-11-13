# Hundred Years’ War

The shared journal is `je_england_1` in `common/journal_entries/england.txt`. The country triggers, round effects, progress bar, scripted buttons, scripted GUIs, and events live in their respective `aoc_hundred_years_war` files.

## Starting subject rulers

The 11 November 1444 subject roster comes from `common/history/diplomacy/00_subject_relationships.txt`. The ruler history and templates are in their respective `aoc_hyw_subjects.txt` files.

| Crown | Subject | Starting ruler |
| --- | --- | --- |
| France | Orléans | Charles I d’Orléans |
| France | Armagnac | Jean IV d’Armagnac, titular count during the royal occupation |
| France | Auvergne | Bertrand V de La Tour, count of Auvergne |
| France | Foix | Gaston IV de Foix |
| France | Bourbonnais | Charles I de Bourbon |
| England | Normandy | Richard of York, royal lieutenant |
| England | Aquitaine | William Bonville, seneschal |
| England | Maine | Edmund Beaufort, governor |

The English subject tags represent local administrations under Henry VI. Normandy’s starting Richard of York and England’s later Wars of the Roses character use separate game objects. Where only a birth year is available, the templates use 1 January as a placeholder. [BnF catalogue](https://catalogue.bnf.fr/ark%3A/12148/cb120297092) · [Armagnac occupation](https://etheses.durham.ac.uk/id/eprint/15421/) · [1444 Bourbon charter](https://actesprinciers.huma-num.fr/corpus/Bourbon/Charles_i/1444_06_20a) · [Foix archives](https://una-editions.fr/les-chartriers-des-foix-bearn-a-la-fin-du-moyen-age/) · [York’s lieutenancy](https://www.dib.ie/index.php/biography/richard-york-a7664) · [Gascon Rolls](https://gasconrolls.org/en/research-tools/duchy-office-holders/seneschals-of-gascony-of-aquitaine-after-1360-1273-1453/index.html) · [Maine commission](https://kinghenryvi.com/1438/)

## Involvement and actions

- England, France, and their direct and indirect subjects are involved. French appanages begin neutral. Outside countries participate through an accepted invitation or a qualifying alliance or defensive pact with one crown. Their journal involvement ends when they lose or withdraw support. Crown subjects can remain involved while neutral.
- **Withdraw from the Hundred Years’ War** is available to outside participants between campaigns. Withdrawal cancels the pledge and suppresses invitations and treaty-derived support for five years. Ordinary alliances and wars continue under the normal diplomacy rules.
- Explicit pledges lapse if relations fall below zero, the supporter becomes a subject, or it becomes an enemy of its crown in a play or war. AI treaty-derived supporters also withdraw for five years if relations turn negative or they fight the crown. The weekly update and campaign start review existing pledges. A summons rechecks eligibility before joining, and withdrawal does not remove a country from a war already underway.
- Open **Invite to War** in the Hundred Years’ War journal as France or England. Invitations are available between campaigns with a six-month cooldown. The picker shows when there are no eligible targets. Invite to War requires at least 50 Relations and Engaged or higher interest from the inviting crown in the target capital's strategic region. The target can have any interest tier in the crown's region. Invitations, Influence French Subjects, Grant Subject Titles, and Promote to Appanage use eligible-only three-column flag pickers. Influence targets French appanages. Grant Subject Titles and Petition France to Confirm Privileges use the French subject check, which requires a direct overlord of France and excludes France itself.
- **Promote to Appanage** uses `change_subject_type` on a recognized direct French vassal that fits the appanage rank limits. Promotion is available between campaigns and retains France as overlord. The subject follows the appanage neutrality and pledge rules immediately after conversion. The next weekly refresh updates the supporter list and force totals.
- Influence raises Liberty Desire and keeps the appanage neutral for five years and through at least the next campaign, unless France restores its support. England pays the appanage £1,000 weekly through the English Subsidy treaty. Its sole article, `aoc_hyw_subsidy_payment`, blocks manual withdrawal by both parties and expires when the 12-month binding period ends. Subsidies already active in older saves retain their original article.
- Titles and accepted petitions to confirm privileges secure a pledge for the next campaign. Their treaties specify £1,000 weekly and a 12-month binding period. AI actions and event responses use the same eligibility rules as player actions.
- Appanages have no autonomy steps. France can grant independence, and an independence play can restore the Appanage relationship if France wins. The privilege petition secures a military pledge without changing the subject type.
- In game, check that the subject relationship displays **Appanage** with the Personal Union icon and that France's subject action reads **Grant Independence**. After using Influence, check that England and the appanage can see the English Subsidy, neither can withdraw, and the treaty and weekly payments end automatically after 12 months. These checks are pending.
- England can claim the French throne before the first campaign. The claim gives 75 Infamy, applies a −100% Infamy decay modifier until conclusion, and adds 0.5 monthly peacetime Tension. All journal outcomes call `aoc_hyw_conclude` to remove the decay modifier.

## Campaigns and settlements

- The Surrender of Maine targets England after a delay. Ceding Maine lets France annex `MIE` and gives England −20% Prestige and −10 Legitimacy for ten years. Refusal adds 0.5 monthly peacetime Tension. France receives its own event for either answer.
- Tension rises by 1 per month in peace and falls by 3 during the campaign’s play or war. At 100, the journal opens its scripted play when the crowns are free to fight. Eligible supporters receive a summons. Refusal costs 75 Relations with the summoning crown and triggers the same five-year withdrawal for an outside supporter. Outside countries already at war with the crown cannot answer a stale summons.
- Enforcing the campaign demand scores a win. A round with no sole winner scores a stalemate. Three wins decide the settlement, and three stalemates conclude the journal with the existing borders and subjects.
- England keeps its holdings and imposes a 25-year treaty with French payments and investment rights. If England claimed the throne, France also becomes its junior partner. A French victory transfers England’s own holdings in geographic France and annexes English subjects with holdings in that region.

## National event viewer

Run `node tools/build_nation_content.cjs` after editing an event. The generator discovers visible, localized country events from national namespaces and positive country triggers. For shared chains and events whose recipient is supplied by the caller, use `tools/nation_event_catalog.json` to list the recipient tags and optionally write a player-facing condition. England lists The Surrender of Maine under Hundred Years’ War. France lists The Keys of Le Mans and Maine Withheld in its Events tab. The generated seen marker records the event for its recipient when it opens.

Use vanilla's `fire_only_once = yes` for unique historical events. Keep eligibility in the event trigger and let the journal handle scheduling and progression. The Maine scheduling flag is set before the six-month delay so subsequent monthly pulses cannot queue another copy. Use a real cooldown for recurring events that need a minimum interval between appearances.

## French AI

France prioritizes protecting its subjects and improving relations with them. Its diplomatic strategy suppresses aggression, annexation, and autonomy reduction against its own subjects. In Europe, France values potential supporters and existing regional interests. Outside Europe, diplomacy focuses on regions where France or a direct subject holds territory. West African interest scores are suppressed before France has a foothold there, and the Canadian, Atlantic and Caribbean priorities retain their existing unlocks.

## Diplomatic play restrictions

Ordinary plays between two journal participants are gated before launch. The check uses live involvement rules and the conclusion flag. Outside countries can interact through ordinary plays, and `dp_aoc_hyw` is exempt.

The initial `INJECT` into vanilla play definitions allowed the play to start in the reported test. A start hook and weekly cancellation ended prohibited plays after creation and were removed. The current `zz_aoc_hyw_play_restrictions.txt` uses explicit `REPLACE` definitions that preserve the installed 1.15 vanilla fields and add the shared guard to `possible`. The English Dominion play uses the same guard directly. Compare these overrides against the installed vanilla definitions when upgrading Victoria 3 or changing compatibility with another mod that replaces the same entries.

After restarting Victoria 3, verify that the ordinary play action is unavailable before confirmation for England against France, both crowns against involved subjects, and an invited participant against another participant. Check the tooltip, an outside-country target, a scripted campaign at 100 Tension, and ordinary plays after conclusion. Static checks confirmed the overrides and removal of cancellation. The latest pre-launch behavior still needs in-game verification.

## In-game regression checks

- Start a fresh 1444 campaign as France and check that **The Hundred Years War in France** opens once on entering the map. Its only choice is **We shall be victorious!**
- Start as England and check that Henry VI rules while **The Wars of the Roses** is inactive. Resolve the Hundred Years’ War through either victory or a stalemate and check that the English journal activates and opens its first event. Reload a legacy save with an active or settled dynastic crisis and check that the crisis keeps its progress or settlement.
- As Castile, accept England’s invitation and confirm the English roster and force totals include Castile. Start an ordinary English play against an outside country such as an Irish minor and back its target. Once Castile opposes England, check that the pledge disappears by the next weekly refresh and that Castile receives no English summons. Repeat with negative relations and no war.
- Manually withdraw as an invited country and as a treaty ally. Check the roster, the journal, the continued diplomatic treaty, and the five-year suppression. Check that a French or English subject cannot withdraw and that an appanage can still be involved while neutral.
- As France, promote a recognized direct vassal. Check the appanage pact, unchanged overlord, eligibility for titles and influence, and the next weekly roster. Confirm that stale picker rows disappear if the subject changes type or overlord while the picker is open.
- In an observer start, check French attitudes, relations actions and play goals toward its appanages. Check that France favors European diplomacy over Dahomey before a West African foothold and retains its colonial priorities when their unlocks are met.

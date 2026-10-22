# Historical power blocs

New games start with Mandate of Heaven (CHI), Irish Clans (TYR), and Sunni
Caliphate (MAM), alongside the existing Holy Roman Empire and Japanese Shogunate.
The game-start on-action enrolls China's subjects, countries with Irish primary
culture, and countries with Sunni state religion, respectively. Countries already
in a bloc are not moved; Chinese subject membership takes precedence.

The three new identities start with Police Coordination I. Every other principle
group blocks these identities; Police Coordination is primary and retains all
three vanilla levels. Existing HRE and Japanese principles remain unchanged.

Sunni Caliphate mandate progress depends on bloc rank and member ranks, without
an independence penalty. Its cohesion target starts at 50 and loses 5 points for
each participant with a non-Sunni state religion, including the leader, down to
a minimum of zero. Joining/leaving previews include the religious penalty.

Normal power-bloc formation is disabled in `can_form_power_bloc`. Generic
identity definitions remain loaded, but are hidden and unavailable, preserving
references from vanilla scripts and principles. The mod's history file replaces
vanilla starting blocs.

Mandate of Heaven blocks the leader's leave/disband action and is exempt from
the weak-bloc rule. This does not preserve a country that is annexed or eliminated.
Future events may call `aoc_create_mandate_of_heaven = yes` in the selected
emperor's country scope. The effect refuses to create a second Mandate, starts
with Police Coordination I, and enrolls that emperor's subjects. No recurring
recreation event is installed.

English localization is in `localization/english/uyr_power_blocs_l_english.yml`.

Validation: script brace balance, principle-group restrictions, history identity
references, icon/background paths, and localization keys/BOM checked locally.
An in-game new-campaign smoke test is still needed to verify startup membership,
the disabled formation/disband actions, and upgrades to Police Coordination III.

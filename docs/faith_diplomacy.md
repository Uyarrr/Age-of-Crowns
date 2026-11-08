# Faith and imperial diplomacy

New cooperative treaties use the evaluating country's state religion and the partner's state religion. Exact faith adds 16 acceptance (Sunni–Sunni, Catholic–Catholic); different faiths in the same organized tradition add 5 (Sunni–Shiite); different traditions subtract 8 (Sunni–Catholic). Atheist countries receive no faith score. The score applies once to a new treaty containing an alliance, defensive pact, guarantee, support for independence, military access, investment rights, noncolonization agreement, tariff concession, trade privilege, or embassy. It does not apply to active treaties or deals with one-time articles.

The implementation adds `aoc_faith_treaty_acceptance` to the vanilla `static_treaty_acceptance` script value. The latter is copied into the mod because Victoria 3 does not merge individual script-value blocks. Review it against the installed game file after game updates.

The Holy Roman Empire's leader can join the defending side when an outsider attacks a bloc member without first declaring a strategic interest in that region. Austria's existing imperial strategy gives that defense a +1000 support score, opposes the outside attacker by -1000, and stays neutral in internal member disputes. The eligibility rule applies only while the bloc has the HRE identity and the leader is in office.

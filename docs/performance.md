# Tick-rate investigation, 6 November 2026

The local Victoria 3 logs from the 02:21 session show a recurring script error:
`has_law_or_variant trigger [ Given law is a variant, we expect the parent ]`.
The retained error.log and five rotated error logs contained 10,992 occurrences
when sampled. Most pointed to land-and-labour political movement lines 574 and
604. These are frequently evaluated support/radicalism calculations. Counts
exclude the duplicate messages in game.log.

Corrected 12 invalid operands across political movements, pop support, and the
shared movement triggers. Variant-specific conditions now use `has_law`, keeping
the named variant as their target. Replacing the operand with its parent would
broaden conditions such as the English enclosure bonus to other tenant-farmer
laws. Valid parent-law `has_law_or_variant` checks remain in place.

Run `node tools/audit_performance.cjs` to check for recurrence and parse the
affected files. This is static validation; no tick-rate improvement has been
measured in the game yet.

## Startup-specific lead

`common/history/global/global.txt` grants `organic_development` to every country
for five years. In `common/static_modifiers/uyr_modifiers.txt`, it grants +30
construction and +50% qualifications. This is a plausible contributor to an
early worldwide building/hiring burst that subsides later, particularly near
November 1449. It is a hypothesis, not a measured cause, and was not changed.

The starting state history has 1,488 create_state blocks across 599 owner tags.
These are static history counts, not runtime counts. The screenshot's prominent
market update and AI tasks warrant measuring actual markets and building
activity; reducing country count alone does not establish that those costs have
been addressed. Lock-time values should not be summed as independent task CPU
costs or treated as proof that the named task causes all of its waiting.

## Verification in game

1. Restart Victoria 3 to load the corrected definitions. Check whether new log
   entries still contain the variant-trigger error; retained old messages do not
   establish that the fix failed.
2. Time a fixed interval at speed 5, with the same country, pause state, autosave
   settings, and debug/profiler settings. Compare a fresh November 1444 start,
   the end of the first year, and a point after November 1449.
3. If the initial interval remains slow, run a separate fresh-start comparison
   without the temporary global construction bonus. Do not compare an existing
   save for that experiment: the history modifier is already stored in it.
   Only change the bonus permanently if this comparison supports it and the
   balance effect is wanted.

## Follow-up after the first restart

The user reported no tick-rate improvement and clarified that speed improves
gradually over a longer period. The new logs no longer contained the invalid
law-variant error. That fix did not establish the main performance bottleneck,
and the five-year construction bonus is a weaker explanation for the observed
timing than initially suspected.

The new retained error logs contained 2,039 errors at the inherited law
commitment treaty's line 126. Added a local override of the installed vanilla
1.15 file. It uses the mod's manorial economy, peasant levy, uneducated masses,
and no-security laws in place of their corresponding vanilla IDs. It omits
checks against absent health, welfare, and extraction laws and the two
inapplicable council-republic acceptance bonuses. All law_type references in
this override now resolve to the local replacement law set.

The logs also contained 349 state-scope evaluations of the country technology
trigger in the colonization event. Its unnamespaced ID `colonization_rush` was
corrected to `uyr_events.1`, matching its declared namespace, and both on-action
callers were updated. Localization IDs remain unchanged. Whether this resolves
the wrong-scope evaluations requires a restart and fresh log inspection. In
existing saves, the old event's pending references/cooldown may not carry across
the renamed event ID; a fresh campaign is preferable for the comparison.

The latest accessible autosave was England, 1 January 1445, playthrough
`0f957f9e-f436-47eb-9e3c-e1807d3311af`. Its serialized records contain:

| Metric | Count |
|---|---:|
| Pop groups | 9,275 |
| Countries with a market entry | 599 |
| Markets with an owner | 413 |
| States with a capital entry | 1,488 |
| Building records | 4,995 |

Older saves have roughly 14,963–15,930 pop groups near startup and 7,667 in a
1453 save, with 603 markets in each. These are **different playthroughs and
older map/content versions**, so they are a lead for consolidation/settling,
not a controlled benchmark or proof of a cause. Save sizes and internal
invalidation counters are not CPU timings or live object counts.

Use `node tools/profile_save.cjs "C:/path/to/save.v3"` on uncompressed debug
saves to reproduce counts. Compare two saves from the same campaign and mod
revision. The script reads saves without modifying them.

Both the performance audit and the existing content audit pass. The game had
closed before the attempted live tick-display inspection, so no new tick timing
or improvement was measured. The next useful evidence is an early/late tick
profile from the same campaign, preferably sorted by execution time, alongside
the save counts; more speculative simulation changes would obscure that test.

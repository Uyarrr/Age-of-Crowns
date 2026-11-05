# Overseas journal heraldic icons

Six original bitmap badges generated with the built-in `image_gen` tool, one
generation per asset, with transparent backgrounds. They are thematic heraldic
illustrations, not assertions of historically granted coats of arms.

| Journal | Emblem | Runtime DDS |
| --- | --- | --- |
| The Cape of Good Hope | Table Mountain, anchor and waves | `aoc_england_cape.dds` |
| The East India Company | Merchantman, striped field and St George canton | `aoc_england_east_india.dds` |
| Australia and New Zealand | Kangaroo, silver fern and Southern Cross | `aoc_england_australasia.dds` |
| The Hudson's Bay Company | Red cross and four beavers | `aoc_england_hudson_bay.dds` |
| Expand the Royal Navy | Gold anchor, rope and St George pennon | `aoc_england_royal_navy.dds` |
| Dominate the New World | Atlantic globe, compass and laurels | `aoc_england_new_world.dds` |

All six DDS files are saved in
`gfx/interface/icons/event_icons/england_overseas/` and assigned directly in
`common/journal_entries/england_overseas.txt`. Matching completion events and
reward modifiers use the same thematic icons.

Each is a **256 × 256, DXT5 (BC3), straight-alpha DDS texture** with all nine mip
levels down to 1 × 1, matching the existing heraldic icon dimensions. Transparent
padding protects the crowns and scrollwork. Alpha-aware resizing avoids dark
halos around the gold edges. Each finished texture is 87,536 bytes.

`sources/` retains the original generated transparent PNGs. The complete final
prompt set is recorded in [prompts.json](prompts.json), and the original output
filenames are recorded in [generated_sources.json](generated_sources.json).
The shared brief requests a crowned, gilded shield with no text; each subject
brief supplies its unique charge. The existing English shield served as a local
visual reference for scale and treatment; it was not supplied as an edit target.

Rebuild with `python tools/build_england_overseas_icons.py` (requires Pillow).
The build writes the DDS assets and [icon_preview.png](icon_preview.png), a contact
sheet decoded from the finished DDS files, including 64px journal-sized previews.
The DDS files use conventional DXT5 headers and decode directly, without a DX10
extension or an in-memory metadata workaround.

`node tools/audit_england_overseas.cjs` checks the six distinct journal assignments,
asset existence, DDS dimensions, DXT5 format, mip count and exact
payload length alongside the journal/content reference checks. Actual in-game
rendering has not been verified.

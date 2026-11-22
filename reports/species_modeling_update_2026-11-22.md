# Species modeling update — 2026-11-22

This update addresses the unreviewed starter drawings in the species catalog. The catalog has 174 **source labels**, not 174 independently confirmed species: some labels are aliases or have unresolved taxonomy. A drawing exists for every label, but existence is not proof of anatomical accuracy.

- 140 labels have an initial model awaiting refinement.
- 25 have previously refined drafts with unresolved flags.
- 8 have previously reviewed drafts with unresolved flags.
- 1 remains an unreviewed starter: *Bothrops ayerbei*. A published taxonomic note reports the name as unavailable; it needs taxonomic reconciliation rather than an invented distinct morphology.

The work in this update replaced 77 previously unreviewed starters with editable, species-focused initial drafts. These include both qualitative photo-informed drafts and drafts based on published descriptions alone. Each preset records its references, which features were considered, and unresolved limitations. Pilot photographs have provider labels; unless explicitly reviewed, these labels are not independent identification. Images visibly showing severe injury were rejected and excluded from rendering/training.

## Important limits

- No draft has been established as 90% accurate. Many still share the same basic projected pose and use schematic markings, rather than a measured, individually fitted specimen.
- A dorsal/oblique drawing and an illustrative ventral view are not full anatomical views. The underside, tail, head, and color pattern of many labels still require independent images and review.
- Description-based models without healthy local images should be compared with credible living-animal photographs before further anatomical claims. Variations in sex, age, geography, and taxonomy can alter appearance.
- The renderer is procedural SVG; it is not a trained ML model and does not establish relationships between venom composition and appearance.

## Reviewing the models

Open `PhysicalRendererTest/index.html`, choose Procedural model, then select a species. Expand “Modeling observations” and “Evidence and limits” to see the species-specific notes. `PhysicalRendererTest/preset-previews/index.html` contains the generated gallery. `reports/species_modeling_ledger.json` records each label's status and outstanding issues; `config/species_presets/` holds the editable parameter files and sources.

The most meaningful next review compares each draft with identified healthy specimens from multiple views, refines the actual geometry and patterns, and records missing evidence. Do not treat a passing renderer test or a completed preset count as biological validation.

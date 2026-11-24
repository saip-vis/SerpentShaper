# Venom profile inventory

This is a structural inventory, not confirmation of biological accuracy. Source labels may be synonyms or subspecies, and image links are not specimen-matched.

- Rendering source labels: **174**.
- Labels with at least one structurally eligible proteomics profile: **149**; without one: **25**.
- Labels with at least one eligible profile and a recorded location: **130**.
- Profiles linked to presets: **356**, including **276** structurally eligible proteomics rows.
- Profiles tagged as dataset-level citation only: **356**. Profiles with unreconciled source taxonomy: **356**.
- Labels with at least one held profile: **15**. Known specific category issue: **1** label (black mamba NP).

A boomslang transcriptomic row has a possible sample-location mismatch with its candidate primary study; see the detailed audit and [pilot source review](research_updates/pilot_five_species_review.md).

## Labels without an eligible measured-protein profile

These may have transcriptomic, unknown or held records. They are not necessarily unstudied in the wider literature.

- *Ahaetulla prasina*
- *Austrelaps labialis*
- *Azemiops feae*
- *Boiga irregularis*
- *Borikenophis portoricensis*
- *Bothrops fonsecai*
- *Bothrops moojeni*
- *Calliophis bivirgata*
- *Calliophis intestinalis*
- *Calloselasma rhodostoma*
- *Cerberus rynchops*
- *Conophis lineatus*
- *Drysdalia coronoides*
- *Echis coloratus*
- *Echis pyramidum*
- *Hydrophis cyanocinctus*
- *Macrovipera mauritanica*
- *Micrurus fulvius*
- *Philodryas olfersii*
- *Tantilla nigriceps*
- *Thamnodynastes strigatus*
- *Thelotornis mossambicanus*
- *Trimeresurus nebularis*
- *Vipera ammodytes*
- *Vipera anatolica*

## How to use this inventory

The [machine-readable audit](venom_profile_audit.json) lists each preset and its profiles, measured versus missing UI controls, source rows, locations and blocking issues. Counted controls reflect reporting, not biological completeness; blanks remain unknown. “Structurally eligible” is not scientific verification.

Research the primary literature, reconcile current taxonomy and source names, record sample origins and methods, and resolve conflicts per sample. Add a newer sample as a separate profile rather than merging values across different animals or experiments. Document revisions and retain original measurements. No venom profile here is validated as predicting a photographed snake’s appearance.

Initial research on two missing-profile labels is recorded in [missing-profile candidates](research_updates/missing_profile_candidates.json). These leads are incomplete and are not ingested or approved for training.

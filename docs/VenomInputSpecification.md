# Venom input specification

Version 0.1.0 — input controls implemented; phenotype output contract remains a draft. November 18, 2026.

SerpentShaper lets a user change venom composition and explore a hypothetical snake concept. Inputs are measured ingredient categories. Evidence supplies context; separately documented species traits and explicit creative decisions supply the visual design.

The catalog drives the local composition editor's grouped controls and explanations. It adds no correlation analysis, learned model, or anatomy prediction.

## The initial controls

The four primary controls are **3FTx, PLA2, SVMP, and SVSP**. These families form a useful first vocabulary, consistent with the [2017 composition review](https://pmc.ncbi.nlm.nih.gov/articles/PMC5618223/). Additional named categories are accessible as advanced inputs; all other source categories remain available in the underlying data.

| Control | What it means | Important boundary | Generation role |
|---|---|---|---|
| **3FTx — Three-finger toxins** | A protein-family proportion | Neurotoxins and cytotoxins are not interchangeable. Total 3FTx does not resolve their proportions. | Retrieve relevant subtype evidence and documented reference profiles. |
| **PLA2 — Phospholipases A2** | The source PLA2 family proportion | A family total is not a direct measurement of neurotoxicity, activity, or onset time. | Introduce relevant reference profiles; do not automatically choose a taipan phenotype. |
| **SVMP — Venom metalloproteinases** | A source protein-family proportion | Class totals and disintegrin-containing proteins need source-specific accounting. | Allow several reference anatomies rather than a fixed viper shape. |
| **SVSP — Venom serine proteases** | A source protein-family proportion | The label does not determine a specific target or net clotting effect. | Retrieve applicable functional evidence before explaining the concept. |

The [2022 African venom study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9744630/) provides checked locators for subtype distinctions, functional assays, and measurement conventions. The machine-readable evidence register distinguishes background discussion from newly measured whole-venom assays. Neither is direct evidence that a percentage causes an anatomical trait.

| Advanced control | Exact source label | Boundary to preserve |
|---|---|---|
| Kunitz-type proteins | KSPI | Not every member should be identified as a dendrotoxin. |
| C-type lectins | CTL | Keep separate from CLP (Snaclec) until source definitions are reviewed. |
| C-type lectin-like proteins | CLP (Snaclec) | Also distinct from the workbook's separate CLP column. |
| Cysteine-rich secretory proteins | CRiSP | No universal functional effect assigned from the family total. |
| L-amino acid oxidases | LAAO | Proportion is not a measurement of enzymatic rate. |
| Disintegrins | DIS | Check whether the source separately counts them or includes relevant proteins within SVMP. |
| Natriuretic peptides | NP | Do not automatically combine NP, C-NP or BNP. |
| Bradykinin-potentiating peptides | BPP | Keep separate from NP and ambiguous peptide categories. |

Functional primary-source curation is still pending for several advanced controls. Definitions and original source IDs are usable before that work is complete; missing evidence must remain visible instead of being replaced with a guessed mechanism.

### Categories outside the initial controls

- The catalog maps 12 controls to 12 distinct existing toxin IDs. It does not reinterpret or merge the other 118 source categories.
- `No ID` remains an unidentified-component observation. It cannot drive a phenotype interpretation.
- Importing a source profile preserves every original category, including categories outside the initial controls. Do not drop those categories and rescale the remainder.
- If a user has allocated 80%, show **20% unallocated**. That balance is an editing aid, not 20% measured unidentified venom.
- The 12-control view is a usability choice, not a claim that all relevant venom chemistry is represented by those categories.

## What a user can adjust

Each control is a percentage in the range 0–100. Store values in percentage points: 25 means 25%, not 0.25. Show the assigned total and unallocated balance. Do not adjust other controls silently when a user changes one value.

A complete custom composition must total 100% ±0.01 percentage points. Blank means missing and must be resolved or removed before submission. Explicit zero is different from missing. Historical profiles keep their original values and the cleaning pipeline's separate review rules. Transcriptomic records remain gene-expression evidence, not protein-abundance presets for a custom venom mixture.

Do not expose “fast-acting,” “deadly,” “neurotoxic,” or “hemotoxic” as interchangeable composition inputs. Those words describe effects, kinetics or potency rather than the measured families in the data. Supported effects can appear in the explanation with their experimental context.

## Subtypes and overlap

Version 0.1 has no independently adjustable child controls. This avoids counting both a family total and a child contribution as separate ingredients.

Before adding subtypes:

1. Define their molecular identity and measurement basis.
2. Check that the source reports separately quantified, mutually exclusive categories.
3. Make children allocations *within* the parent total. Children plus a source-defined unspecified remainder must equal that parent amount.
4. Record the evidence and exact original measurements. Broad functional tags are not automatically mutually exclusive subtypes.

For example, 60% total 3FTx cannot establish how much is alpha-neurotoxin. Do not manufacture a split from the total or treat alpha-neurotoxicity as an additional 60% ingredient.

## How composition influences a snake concept

The intended route is:

**Composition → contextual evidence → reference profiles → separately sourced traits → hypothetical design.**

Each proposed physical or ecological trait has one origin:

| Origin | Required information | How it is presented |
|---|---|---|
| `documented_reference` | Reference species, trait value, source URL and locator | A trait borrowed from a documented real species, not inferred as inevitable from venom. |
| `creative_choice` | Trait value and design reason | An explicit artistic choice compatible with the selected concept. |
| `unresolved` | Missing value and explanation of the gap | Leave unspecified rather than invent an evidence-backed answer. |

Potential design fields include body proportions, head and tail shape, coloration, pattern, habitat and diet. **No direct percentage-to-anatomy rule is currently supported or implemented.** A morphological resemblance requires its own trait reference; a composition citation alone is insufficient. Evidence from a mammalian assay does not automatically transfer to a particular wild prey species.

Changing an ingredient may change the supporting examples, explanations and available design references. It need not change every visible trait. Preserve user-locked creative choices when they remain applicable, and explain changes in reference selection. There is no justified “increase PLA2 by 10%, lengthen the snake by 10%” rule.

Evolution text must describe a hypothetical scenario and its supporting analogies. A generated animal has no observed evolutionary history.

### Concrete reference examples already in the database

These are existing measured profiles, not generated designs, ecological claims, or species predictions:

| Source row | Reference species | Example ingredient value | Why it is useful |
|---|---|---|---|
| 286 | *Naja naja* | 3FTx 96.9% | A real 3FTx-rich composition example. |
| 306 | *Oxyuranus scutellatus* | PLA2 79.4% | A real PLA2-rich composition example. |
| 191 | *Dispholidus typus* | SVMP 77.5% | An SVMP example outside a stereotyped viper body plan. |
| 299 | *Ovophis convictus* | SVSP 52.94% | A real SVSP-containing composition example. |
| 189 | *Dendroaspis polylepis* | KSPI 61.1% | A real Kunitz-type composition example. |

All refer to `RAW_DATABASE_VENOM` in [the 2023 dataset](https://doi.org/10.6084/m9.figshare.22179949.v1). Each number belongs to one source row, not every member of that species. No traits have been borrowed from these species in this implementation.

## Files and implementation boundary

- `config/venom_input_spec.json`: control IDs, original-data bindings, definitions, boundaries, interpretation and phenotype policies.
- `evidence/input_evidence.json`: eight seed evidence records with source locators and limitations. Several are nomenclature or source-structure records; they are not all functional experiments.
- `schemas/snake_concept.schema.json`: draft JSON Schema for future concepts, including required citations for documented reference traits and explicit creative/unresolved origins.
- `scripts/validate_input_spec.py`: dependency-free checks for source bindings, evidence references, and traceability of the five example profiles.

The JSON Schema is a design contract, not a runtime feature of `InitialInterfaceTest.py`. A standards-compliant JSON Schema validator must be integrated before using it as an API validation boundary. Application logic must additionally check unique component/trait IDs, valid catalog references, total percentages, evidence scope, genuine citations, and source-profile status. Schema shape alone cannot establish those facts.

The interface now provides primary/advanced grouping, help text, source references and live percentage accounting. The original profile browser retains every source category. Profile-based drafts preserve all 130 entries while permitting edits only to catalog-bound categories. See `InitialInterfaceTest.md` for the API and retention rules. The legacy raw-label API remains available for compatibility.

# Physical reference profiles

Start with [the complete catalog outline](physical_profiles/AllSpeciesPhysicalProfiles.md). It has a species index and an entry for every one of the 174 source labels, including labels without downloaded photos. The original [four starter profiles](StarterSpeciesPhysicalProfiles.md) remain available.

The engine-readable export is `data/processed/morphology/physical_profiles.json`. Join its `profiles` to the species catalog using `species_id`. Each record retains the exact source label, pilot-folder paths, venom-profile IDs, compiled physical traits, supplementary descriptions and proposed rendering controls.

## Current coverage

- 174 catalog entries.
- 170 exact-name or existing documented-alias matches to the ReptTraits v1-2 workbook.
- 149 entries with supplementary physical-description traits, including the original four starters. This means at least one extracted descriptive field, not a complete or independently verified phenotype.
- 25 entries currently rely on compiled traits or taxonomic cautions. Their unextracted anatomy fields remain null and are listed in `reports/morphology_coverage.json`.
- 7 entries have juvenile SVL values whose column header says maximum while the workbook definition says mean. Values are preserved with `needs_review`; they are not used as measurements of a typical juvenile.

The four unmatched workbook labels are Bothrops colombiensis, Calliophis bivirgata, Macrovipera mauritanica and Thamnodynastes strigatus. Alternative spellings or generic placements exist for some, but this export does not silently create new taxonomic joins. Some already have independent descriptive sources. Bothrops colombiensis also has unresolved species boundaries.

## Evidence and limitations

ReptTraits is a published compilation, not a new measurement campaign. Values retain workbook sheet/cell addresses and the trait-specific citation strings. The original bibliography and relevant rows are preserved in `sources/morphology/repttraits_catalog_extract.json`. Source publication: Oskyrko et al. (2024), [Scientific Data](https://doi.org/10.1038/s41597-024-03079-5); [dataset](https://doi.org/10.6084/m9.figshare.24572683).

`config/morphology_notes.json` contains the editable descriptions and source URLs. They are concise reference summaries drawn from taxonomic studies, museum and university accounts, government field guides and specialist accounts. Their depth and geographic scope vary. Search-discovery caches include unselected results; a search hit is not automatically evidence. Only the curated notes and pinned workbook extraction feed the export. Some sources were available as indexed extracts rather than fully retrieved publications. These profiles are a first reference pass, not expert-approved species diagnoses.

Compiled maxima are not typical adult lengths. SVL excludes the tail. Colors and patterns in ReptTraits are coarse and can omit known variation; keep those categories separate from the descriptive notes. Existing starter accounts sometimes give different maximum lengths. Both source values remain visible rather than being averaged or overwritten. The green color category reported for Bothrops barnetti requires corroboration before use as a palette.

Species-complex flags are retained, including king cobras, forest cobras, the eyelash-viper group and historical godmani labels. The Hypnale hypnale profile flags conflicting snout descriptions between a public guide and a taxonomic revision. No numerical snout parameter is assigned.

The `rendering_proposals` section lists independently adjustable design controls without numeric defaults. Unknown traits are never filled from a relative. Body ratios, calibrated colors, population distributions and venom-to-trait mappings are null. These references do not describe the particular animals photographed for the image pilots. Existing injury exclusions, acceptance decisions and image manifests are unchanged.

## Rebuild

After editing curated notes or rebuilding the species catalog:

```sh
python3 scripts/build_physical_profiles.py
```

This uses the cached extraction and verifies its SHA-256 against the original workbook. If the workbook changes, refresh it using Python with openpyxl installed:

```sh
python3 scripts/build_physical_profiles.py --refresh-extract
```

The bundled Python environment used for this project already has openpyxl. Refreshing only reads the workbook and exports JSON; it does not edit the XLSX. Rebuilds require local source data and never fetch websites or approve photos.

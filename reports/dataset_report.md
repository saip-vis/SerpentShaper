# SerpentShaper dataset discovery

Research date: November 17, 2026. Counts below come from the actual downloaded files unless identified as publication claims. Taxon-label counts are not reconciled counts of accepted species. Paths are relative to the project root.

## Recommendation

Use the MuseumVenomics published-proteome CSV as the initial composition reference, ReptTraits v1-2 for species traits, and Squamatabase for cited diet observations. Supplement selected Colubridae from primary studies. Atractaspididae remains a measured-composition coverage gap: a relevant transcriptomic study was downloaded, but no comparable comprehensive quantitative secreted-venom dataset was verified in this search.

This collection supports SerpentShaper's evidence and reference layer. It does not establish that a venom profile uniquely determines appearance, habitat, or behavior. Biological references and creative visual choices should remain distinguishable.

## Downloaded composition sources

### 1. MuseumVenomics published profiles — recommended starting point

- Source: [author repository](https://github.com/DEsquerre/MuseumVenomics).
- File: `data/raw/museum_venomics/PublishedProteomes.csv`.
- Download pinned to repository commit `44f7965fc77f019da1f3cba59ebb2effec3739c9`; the commit metadata is saved.
- **413 profiles and 220 distinct taxon labels**: Elapidae has 199 profiles / 90 labels; Viperidae has 214 profiles / 130 labels.
- Each row includes toxin-family proportions, taxonomy, reported total, analytical technique, reference, and DOI. No row has an empty DOI field; DOI resolution and correctness have not been checked row by row.
- Reuse: repository license and README state **CC0 1.0**; both are saved. Cite the authors and underlying studies.
- **Limitations:** no Colubridae or Atractaspididae rows. Some labels include subspecies or differing taxonomic treatments. Nineteen reported totals fall outside 95–105%; these are review flags, not proof of errors. Parent families and subcategories coexist, so summing every numeric column would double-count components. Do not automatically reinterpret source zeros as confirmed biological absence.

### 2. MuseumVenomics experimental profiles — keep sample types separate

- File: `data/raw/museum_venomics/SummaryResults_ThisStudy.csv`.
- **92 rows / 42 distinct taxon labels**: 32 `MilkedVenom`, 55 `PreservedFixedGland`, and five `FrozenEthanolGland` rows.
- Includes toxin-family percentages, sample metadata, and some length measurements.
- Reuse: same CC0 repository.
- **Limitations:** preserved gland profiles are not interchangeable with secreted venom. The file includes labels requiring taxonomic review. The web-indexed repository documentation used an older filename; the current repository API was used to locate the actual file. Historical failed download attempts remain in the manifest.

### 3. Venom and diet compilation, 2023 — supplementary coverage

- Publication: [Diversity Begets Diversity When Diet Drives Snake Venom Evolution, but Evenness Rather Than Richness Is What Counts](https://doi.org/10.3390/toxins15040251).
- Dataset: [Figshare, version 1](https://doi.org/10.6084/m9.figshare.22179949.v1).
- Files: `data/raw/venom_diet_2023/Supp. Mat. 1.xlsx`, `Supp. Mat. 2.xlsx`, and `Supp. Mat. 3.xlsx`.
- Workbook 1 contains raw venom, diet-family, diet-order, and summary-index sheets. Its raw venom sheet has **356 records / 174 distinct source species strings**. The publication describes 173 species; reconcile labels before quoting an accepted-species count.
- Raw measurement labels: 288 `proteome`, one `proteome `, 58 `transcriptome`, seven `trancriptome`, one `unknown`, and one `proteoje`. Do not silently fix the ambiguous entry without checking the source.
- Selected rear-fanged examples include a proteomic record for *Dispholidus typus*, plus transcriptomic records for *D. typus*, *Boiga irregularis*, *Thelotornis mossambicanus*, and *Philodryas olfersii*. Family assignments must be reconciled under an explicit taxonomy.
- Reuse: Figshare metadata states **CC BY 4.0**.
- **Limitations:** mixed proteomic and transcriptomic evidence; numerous cached spreadsheet errors in derived diversity/diet calculations; some blank metadata headers. Use raw measurements after review rather than importing derived index cells as biological observations. The other two workbooks primarily contain analysis inputs/results, not independent new venom samples. This compilation overlaps other sources.

### 4. Boomslang primary study — selected Colubridae

- Publication: [combined transcriptomic, venomic, and antivenomic analysis of Dispholidus typus](https://pmc.ncbi.nlm.nih.gov/articles/PMC5335903/).
- Original archive: `data/raw/boomslang_2017/supplementary.zip`.
- Verified archive member `mmc1.xlsx` contains three sheets. The article describes Supplementary Table S1 as protein identification and quantification.
- Full article XML: `sources/PMC5335903.xml`.
- Reuse: article states **CC BY 4.0**; retain attribution and source context.
- **Limitations:** this is protein-level/peak-level supplementary material, not an already harmonized one-row-per-species training table. Aggregate only after reviewing its layout and units. Its biological sample may overlap compilation records.

### 5. Sub-Saharan African venoms, 2022 — composition and functional evidence

- Publication: [High-throughput proteomics and in vitro functional characterization of the 26 medically most important elapids and vipers from sub-Saharan Africa](https://pmc.ncbi.nlm.nih.gov/articles/PMC9744630/).
- Original archive: `data/raw/african_venoms_2022/supplementary.zip`; article XML also saved.
- Verified nested archive `giac121_supplemental_figure_and_table.zip` contains `TableS1-Supplementary Material revision.xls` and `FigureS1.pdf`.
- Reuse: article states **CC BY 4.0**.
- **Status:** downloaded and archive contents verified; the legacy XLS table has not been parsed or counted. The publication's 26-species scope is not a new independently verified row count. Useful next-stage source for connecting composition to measured functions, preserving assay conditions.

### 6. Atractaspis aterrima, 2013 — supporting transcriptomic evidence

- Publication: [Atractaspis aterrima Toxins](https://pmc.ncbi.nlm.nih.gov/articles/PMC3847709/).
- Files: `sources/PMC3847709.xml` and `data/raw/atractaspis_2013/supplementary.zip`.
- Supplementary archive includes `toxins-05-01948-s001.pdf`; main article Table 2 lists expressed snake-related toxins.
- Reuse: article states **CC BY 3.0**.
- **Limitations:** venom-gland transcriptomics, not a validated quantitative secreted-venom composition table. Keep it outside the measured-proteome subset. It supplies evidence for the Atractaspididae reference layer without closing the composition-data gap.

### 7. Foundational 2017 review — source and bibliography

- [A Review and Database of Snake Venom Proteomes](https://pmc.ncbi.nlm.nih.gov/articles/PMC5618223/).
- Full article and its embedded tables saved as `sources/PMC5618223.xml`.
- The publication reports 132 species overall, including five non-front-fanged species; that does not mean its three main tables provide a complete standardized record for all 132.
- Reuse: **CC BY 4.0**. Overlaps later compilations; use to trace original references, not as an independent batch of samples to append blindly.

## Downloaded ecology and morphology sources

### ReptTraits — recommended species-trait reference

- Publication: [ReptTraits](https://doi.org/10.1038/s41597-024-03079-5).
- Dataset: [Figshare version 4](https://doi.org/10.6084/m9.figshare.24572683.v4).
- Both original `ReptTraits dataset v1-1.xlsx` and `ReptTraits dataset v1-2.xlsx` are saved in `data/raw/repttraits/`. Use **v1-2**: its change sheet explicitly corrects habitat/microhabitat entries for some snakes.
- The v1-2 Data sheet has **12,060 reptile rows, including 4,073 labeled Serpentes**. Its taxonomy includes 398 Elapidae, 383 Viperidae, 69 Atractaspididae, and 2,105 Colubridae rows. These are trait records, not venom profiles, and taxonomy may differ from other sources.
- Contains habitat/microhabitat, diet, length/mass, and other traits, with separate definitions, per-value sources, and references.
- **170 of the 220 published-proteome taxon labels match exactly** to a snake name in this file. This is a preliminary name overlap, not assurance that every matched trait is populated or a validated taxonomic join.
- Reuse: **CC BY 4.0**.

### Squamatabase — cited prey observations

- Source: [author repository](https://github.com/blueraleigh/squamatabase); [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7125237/).
- Saved `diet.csv`, README, package description, and field documentation under `data/raw/squamatabase/`, pinned to the downloaded commit recorded in `sources/squamatabase_commit.json`.
- Actual downloaded CSV has **11,057 rows / 1,481 distinct predator labels**. Repository prose describes a larger archive; use the audited file count for this snapshot.
- Contains predator/prey identities, some size and age information, locality, event context, and references. Entries are source records and may describe multiple prey items, so row count is not necessarily event or individual count.
- **82 of the 220 published-proteome labels match exactly** to predator names in this snapshot. Other matches may become possible after taxonomy reconciliation.
- Reuse: package description states **CC0**.

## Located but not downloaded

- [2021 venom/environment dataset](https://doi.org/10.5061/dryad.nzs7h44qs): repository describes 112 elapid/viperid taxa and ten toxin groups; supporting data are in a DOCX. Metadata and file listing saved, but download returned HTTP 401.
- [SquamBase](https://doi.org/10.5061/dryad.76hdr7t3b): relevant traits, literature records, metadata, and length/mass equations. Metadata/file listings saved; file downloads returned HTTP 401. **SquamBase is a separate resource from Squamatabase.** ReptTraits is already available locally for the initial trait layer.

These are access limitations, not verified absences of data. No account login or restricted download was attempted.

## Next implementation step

1. Design separate profile, component-measurement, species-trait, and evidence/source tables.
2. Establish a toxin-family hierarchy so totals and subcomponents cannot be counted twice.
3. Import the 413-profile CSV with original values and DOI provenance. Flag questionable totals, missingness, and taxonomic names; do not normalize or average them automatically.
4. Separate secreted venom, gland proteomics, and transcriptomics. Deduplicate overlapping studies before combining sources.
5. Join reviewed taxon names to ReptTraits v1-2 and diet observations, preserving per-trait citations and missing fields.
6. Curate selected rear-fanged and Atractaspididae evidence explicitly; keep incomplete coverage visible in the interface.

The article XML and supplementary materials can later seed a RAG corpus after passage/table extraction and citation indexing. No vector index, RAG ingestion, image collection, or training was performed in this phase.

# Five-species venom source review

This focused review identifies study candidates and specific discrepancies. It is not an exhaustive search, does not verify every value in the source workbook, and does not prove row-to-study identity unless an explicit row-level citation exists. The original dataset is unchanged. Photo records are not linked to the venom specimens.

## Black mamba — Dendroaspis polylepis

- Workbook row 189 is a strong candidate match to [Laustsen et al. 2015](https://doi.org/10.1016/j.jprot.2015.02.002), but its 2.9% NP is a serious label conflict: the original figure calls NP non-protein components, whereas a later review calls it natriuretic peptides. This value is masked in the exploratory baselines, trained length experiment and main interface matching; the original remains in the database.
- [Redureau et al. 2025](https://doi.org/10.3390/toxins17050243) provides a separate, more recent pooled Tanzanian sample measured with trypsin-only LC-MS peptide peak areas. Its figure 4D shows 33.48% 3FTx, 55.62% Kunitz-type, 1.02% SVMP, 0.20% hyaluronidase, 0.04% natriuretic peptides and 9.64% Others. The [structured candidate](black_mamba_2025.json) transcribes all displayed groups, not every molecule. Others is a mixed category of non-toxin, cellular and unidentified proteins; it must not be equated with an unidentified-toxin category.
- The publisher's supplementary endpoint returned HTTP 429 during the earlier review. The underlying quantitative table has not been checked. Candidate family mappings and category boundaries remain to be verified; it is not ingested or approved for training.

## Spectacled cobra — Naja naja

- Row 278 is a candidate match to [Dutta et al. 2017](https://doi.org/10.1016/j.jprot.2016.12.018): both report 63.8% 3FTx and 11.4% PLA2. The study is from eastern India; the workbook gives only India. This is strong evidence, not a proven row-level citation, and the other ten rows still require their own source checks.
- A newer primary study, [Bansode et al. 2026](https://doi.org/10.1016/j.jprot.2026.105665), describes Indian cobra venom samples from multiple Indian regions. Its abstract supports regional variation but does not provide an extractable complete quantitative profile here. Full text and supplementary data need review before adding measurements.

## Coastal taipan — Oxyuranus scutellatus

- Papua New Guinea row 305 is a candidate match to [Herrera et al. 2012](https://doi.org/10.1016/j.jprot.2012.01.006): the manuscript reports 68.3% PLA2 for Papua New Guinea and the workbook has the same value. Other matching reported categories strengthen the lead, but the workbook contains no row-level citation. Australian row 306 remains unresolved because candidate values differ.
- A later [2025 comparative study](https://doi.org/10.3390/toxins17100488) used venom provided by Venom Supplies. It describes 66% PLA2 and 9% 3FTx as proportions of identified proteins in its discussion; the abstract also calls them relative abundance. **The measurement denominator and method need clarification before treating these as venom abundance percentages or comparing them numerically with the workbook.** Sample location and pooling were not established in the material reviewed. Do not add as a quantitative profile yet.

## Western diamondback — Crotalus atrox

- Row 127 is a candidate match to [Calvete et al. 2009](https://doi.org/10.1021/pr900249q), including 49.7% SVMP and 19.8% SVSP. The workbook reports location as unknown. The primary source and complete family mappings need review; row 128 is not yet matched.
- [Balchan et al. 2025](https://doi.org/10.1016/j.toxicon.2025.108497) studied five rattlesnakes from Arkansas and compared metalloproteinase activity and abundance with other sampled populations. The accessible abstract is evidence for geographic variation, not a complete family-percentage profile. Do not invent individual values or merge them with the older workbook rows.

## Boomslang — Dispholidus typus

- [Pla et al. 2017](https://doi.org/10.1016/j.bbagen.2017.01.020) is a strong candidate for row 191: both the paper and the workbook report 77.5% SVMP, and the proteomic venom in the paper came from South African-origin specimens. Full-family comparison and direct row attribution remain to be verified.
- The same paper is a strong candidate for transcriptomic row 190: both report 74.64% SVMP among toxin-encoding transcripts, and PLA2 is approximately 7.56% in the paper versus 7.6% in the workbook. **Possible location mismatch:** the workbook labels this row South Africa, while the paper says the single gland specimen used for transcriptomics came from Tanzania. The South African venom used for proteomics was obtained separately. Do not merge the two measurements, label them as paired samples, or silently overwrite the workbook. The match is still an inference.
- [Menzies et al. 2022](https://doi.org/10.1016/j.toxcx.2022.100118) investigated venom effects and inhibitors; it is not, by itself, a replacement full quantitative venom profile.

## Next checks before ingestion

1. Obtain and inspect full quantitative supplementary data when accessible, and document the original figure/table and extraction method.
2. Preserve each sample as its own record, recording specimen count, pooling, location, age/sex when reported, technique, units and sources. Mark unknowns as unknown.
3. Review vocabulary and overlapping categories, original ranges and detection limits, taxonomy, and numerical mapping. Keep reported protein, transcript and functional assays separate.
4. Reconcile the two flagged workbook issues and document decisions without deleting the original values. Only promote a profile when its measurements and provenance are sufficiently documented for its intended use.

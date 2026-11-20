# Image dataset research for SerpentShaper

Research date: November 18, 2026. This is dataset discovery and metadata inspection, not image acquisition or model training.

## Recommendation

Use SnakeCLEF metadata to audit species coverage, and use iNaturalist's documented licensed-image resources to acquire a traceable subset. Investigate standardized museum photographs as supplementary anatomy/color references. Do not start with broad, untracked web scraping.

No broad dataset guaranteeing calibrated, complete 360-degree views of the same individual across the target venom species was verified. Uncontrolled viewing diversity, multiple photographs per observation, standardized dorsal/ventral photographs, and calibrated multi-camera data are different resources.

## Candidate datasets

### SnakeCLEF 2024, reusing the 2023 development data

- [Official dataset page](https://www.imageclef.org/node/319).
- The official page describes 1,784 snake species, observation grouping, and country/venomous-status mappings. Training images are offered at full resolution (~60 GB), maximum 500px (~17 GB), and maximum 240px (~4.5 GB), plus additional rare-class images (~5.1 GB). These are advertised archive sizes, not files downloaded here.
- This is primarily a species-identification collection. Multiple images associated with an observation do not establish calibrated views or comprehensive angle coverage. The metadata inspected has no viewpoint, photographer, or per-photo-license fields.
- The official metadata server failed TLS certificate verification. Verification was not disabled. The official challenge's private test images are not publicly accessible and are not acquisition candidates.
- A public participant mirror supplied the three metadata CSVs over verified HTTPS, pinned to commit `786f6a6a17453a8686d1cb9af7407525292d0d7c`: [mirror location](https://huggingface.co/pengdadaaa/SnakeCLEF2024/tree/786f6a6a17453a8686d1cb9af7407525292d0d7c/metadata).
- Mirror CSV counts: 154,301 iNaturalist training records, 13,843 HerpMapper training records, and 14,117 validation records, totaling 182,261 rows with 1,784 distinct binomial-name strings. These counts are verified for this mirror snapshot, not a claim that every referenced image exists or is usable.
- Original-image terms need verification before generative training. A model/code repository license must not be assumed to license all source photographs.

### iNaturalist Licensed Observation Images

- [Official developer data resources](https://www.inaturalist.org/pages/developers), [AWS open-data registry](https://registry.opendata.aws/inaturalist-open-data/), [official metadata documentation](https://github.com/inaturalist/inaturalist-open-data/blob/main/Metadata/README.md).
- Broad species coverage with photo IDs, observation IDs, species taxonomy, image dimensions, photographer references, quality grades, and per-photo licenses available through linked metadata tables.
- The inspected photo metadata schema does not contain camera-view or angle labels. `position` means photo ordering within an observation, not camera pose.
- Use documented datasets/exports for bulk acquisition. The official developer page says the API is for application development rather than bulk scraping.
- Reuse terms vary per image. Store the actual photo license and attribution rather than relying only on observation-level terms. Prefer a pilot subset with clear, compatible licenses and retain their source pages.
- SnakeCLEF includes iNaturalist material. These are overlapping sources and must be deduplicated rather than counted as independent evidence.

### UMMZ Neotropical snake photographs / Batch-Mask

- [Dataset DOI](https://doi.org/10.7302/qta3-xs67), [Batch-Mask study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9617216/), [publisher article](https://doi.org/10.1093/icb/icac036).
- The study describes a benchmark of 33 species, with standardized photographs, dorsal and ventral views, color references and scale calibration. It describes 151 labeled images and a separate test set of 50 unlabeled photographs; these study counts are not an audited inventory of the entire repository.
- The camera was positioned above the specimen. Multiple illumination directions are not multiple camera angles. This is useful for surface/color/body outline reference, not a general 360-degree reconstruction dataset.
- The institutional landing page could not be read in this environment; complete repository contents, venom-species overlap, and image license terms remain unverified. The paper's open-access license does not automatically settle the underlying dataset's terms.
- Article XML is saved locally under `sources/image_research/batch_mask_article.xml`.

### Specialized multi-camera strike research

- [Primary study](https://doi.org/10.1242/jeb.250347), [data DOI](https://doi.org/10.26180/29567672.v1).
- The study captured strikes for 36 venomous species with two high-speed cameras. Its scope includes 31 Viperidae, four Elapidae and one Colubridae species.
- Inspection of the public dataset API found derived coordinates, tables and analysis scripts, **not the raw multi-camera videos**. The dataset declares CC BY-NC-ND 4.0. Do not describe it as a downloadable general image-training corpus or assume video access.
- Potential reference for future pose/kinematics work, not the recommended first image source.

## Provisional overlap with our venom data

The primary starting list is the **149 distinct source-name strings** in the 276 eligible proteomic profiles of the cleaned 2023 workbook. The broader published compilation contains 220 taxon labels; the two venom sources overlap and are not additive.

| Target list | Labels | Exact matches in mirrored SnakeCLEF metadata | Referenced image records for those names |
|---|---:|---:|---:|
| Eligible proteomic profiles | 149 | 125 | 21,012 |
| Broader published compilation | 220 | 161 | 18,109 |

These image totals use distinct provider/path keys within the metadata. They are not deduplicated visual-content counts and not verified licensed/downloadable image counts. The target lists differ, so their totals must not be added or interpreted as nested.

| Example already used by SerpentShaper | Metadata image records | Observation identifiers |
|---|---:|---:|
| *Naja naja* | 148 | 81 |
| *Oxyuranus scutellatus* | 97 | 43 |
| *Dendroaspis polylepis* | 245 | 127 |
| *Dispholidus typus* | 350 | 175 |
| *Ovophis convictus* | 10 | 5 |

The small *Ovophis* count illustrates why species balance and individual-view coverage need inspection before deciding training feasibility. These records are species-level image references, not photographs of the individuals whose venom was measured.

`coverage_audit.json` contains per-name counts and unmatched names. The 24 unmatched labels in the eligible set need name reconciliation before declaring images absent. Synonyms, misspellings, subspecies, taxonomic changes and actual gaps can all affect exact matching. No names were automatically corrected in this phase.

## Work to do before bulk image acquisition

**2D scope confirmed.** The follow-up [image acquisition gap report](imaging_gaps.md) applies seven documented name crosswalks and checks public iNaturalist metadata for the 38 initially missing/sparse labels. It finds 17 remaining labels without SnakeCLEF matches, 16 with 1–29 image records, and 116 with at least 30. These are acquisition priorities, not reviewed image-quality ratings. Original venom labels remain unchanged; full per-label results are in `imaging_gaps.json`.

1. Choose the first deliverable's visual scope: a 2D generated image/reference sheet can use diverse uncontrolled photographs; a controllable 3D animal needs a different pose/multi-view strategy.
2. Create a stable species/taxon crosswalk between venom records, trait records and image providers. Keep original names and review unresolved mappings. Start with eligible proteomics; do not substitute transcriptomics as measured venom.
3. Define an image manifest before download: image and observation IDs, source URL, original and resolved taxon IDs/names, photo license, attribution, dimensions, quality/review status, framing, viewpoint, pose, and specimen/individual ID when actually known. Record unknown values explicitly.
4. Keep framing separate from view: full body/head/tail/partial is framing; dorsal/ventral/lateral/anterior/posterior/oblique/unknown is a view vocabulary. Coiled or extended is pose, not view. Record who or what assigned each annotation.
5. Set quality and split policies: preserve originals; flag blur, severe occlusion, watermarks, human handling and multiple animals as appropriate; detect duplicates; keep all photos from one observation or known individual together. Later holdout design must match the chosen modeling goal.
6. Pick a pilot of roughly 20–30 well-supported target species and audit suitable photos/views. A planning target of 50–100 distinct usable images per species is a pilot budget, not a validated sample requirement or guarantee of training success. Species with weak coverage remain explicit gaps.

It is not necessary to train a model, resolve all 117 unfamiliar venom labels, or download an entire image archive before starting this pilot. The composition-to-reference/trait evidence work can continue alongside acquisition. Species-labeled photographs still do not directly teach a causal venom-to-anatomy relationship.

## Local artifacts

- `sources/image_research/`: metadata CSVs, primary article XML, provider documentation and dataset metadata.
- `sources/image_research/downloads.json`: download outcomes, URLs, hashes and recorded failures.
- `reports/image_research/coverage_audit.json`: provisional name coverage, counts, and source limitations.
- `scripts/research_image_sources.py`: metadata/documentation acquisition only.
- `scripts/audit_image_coverage.py`: repeatable exact-name overlap audit.

No photos, model weights or training artifacts were downloaded or generated in this phase. The local scripts and reports have not been committed or pushed to GitHub.

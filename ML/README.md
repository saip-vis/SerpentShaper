# ML pilot: venom, references and images

This folder contains exploratory length, visual style, photo-patch color and connected illustration models. It does **not** contain images paired to venom from the same verified individual. Image, venom and morphology records are linked by unreconciled source species names; the photographed snakes are not known to be the sampled individuals. Do not treat these links as individual-level paired training examples or evidence that venom causes a particular phenotype.

The earlier [visual style model](visual_style_model.json) predicts artistic colors and dimensions from authored presets; it remains available in the [research interface](../MainInterface/research-interface.html). The new [connected prototype](learned_morphology/connected_prototype.json) learns shared shape and motif controls from the same authored design collection and includes a small cue from the separate photo-patch color experiment. It does not select a species at inference, measure anatomy from photographs, or predict full-snake appearance reliably. See the [interface notes](../MainInterface/README.md) for use and regeneration.

## Species-wide venom audit

The [species-wide inventory](venom_profile_audit.md) covers all 174 current rendering source labels, including the 149 with structurally eligible proteomics profiles. It records missing evidence and does not claim scientific validation. Rebuild it with `python3 scripts/audit_species_venom_profiles.py`.

The [five-species source review](research_updates/pilot_five_species_review.md) tracks candidate primary-study matches, newer research and unresolved issues. The [2025 black mamba record](research_updates/black_mamba_2025.json) captures its displayed figure groups as a separate staged profile. Run `python3 scripts/validate_staged_venom_profile.py` for structural checks; these do not certify scientific accuracy, approve it for training or add it to the interface/database.

## Current audit

The earlier reproducible snapshot in `data_audit.json` contains 174 source species labels (not necessarily unique taxa), 276 structurally eligible proteomic profiles and 1,213 locally available photo records. Of those labels, 137 had both an eligible proteomic profile and at least one available image at that time. The later [catalog follow-up](../reports/image_research/catalog_followup_2026_notes.md) downloaded 599 additional photos. An assistant conducted a [contact-sheet screen](../reports/image_research/catalog_photo_screen_2026.md) of all 599, rejecting 36 after viewing the originals; 51 of the new photos were subsequently accepted after individual inspection, and 512 remain unreviewed and excluded from training. A visual candidate is a priority for further review, not an acceptance. [Current morphology readiness](learned_morphology/readiness.json) reports the gate counts. Availability does not mean an image has passed the review gate.

`pilot_manifest.json` selects five source labels for an initial comparison:

| Source label | Eligible proteomic profiles | Accepted images | Distinct observation groups among accepted images |
| --- | ---: | ---: | ---: |
| *Naja naja* | 11 | 0 | 0 |
| *Oxyuranus scutellatus* | 2 | 5 | 4 |
| *Dendroaspis polylepis* | 1 | 7 | 4 |
| *Crotalus atrox* | 2 | 8 | 7 |
| *Dispholidus typus* | 1 | 0 | 0 |

The earlier user approval of the coastal taipan and black mamba pilot folders has been recorded for their previously unreviewed images; pre-existing rejected black mamba records remain excluded. After follow-up review, four images of one severely damaged taipan were rejected, and one near-duplicate image from another observation was held out. Two user-accepted diamondback photos of the same observation are held from training because their visible tail condition could not be resolved. The user’s species review is preserved; no injury diagnosis is asserted. The 20 eligible records within the five original pilot source labels span 15 observation groups, not necessarily 15 independent individual snakes. The Naja naja and boomslang pilot images remain unreviewed in the machine-readable manifest. Five additional photos from other source labels were subsequently reviewed and accepted for visible body evidence; their provider-assigned identities are not independently verified. The patch-color experiment assigns photo evidence to leave-one-genus-out folds; the full morphology model has no image-trait training set yet. [Image review notes](pilot_image_review.json) distinguish full-body and head-only views, visibility issues, juveniles and items needing follow-up. Several user-accepted records have advisory quality flags; acceptance and training suitability are not identical.

A [provider metadata snapshot](pilot_metadata_snapshot.json) covers the 50 original pilot photo records: the API returned every photo and each reported license code matched the stored code. This is a metadata comparison, not species identification or legal clearance. License codes, source pages and attribution are preserved in the manifest. The original metadata did not record a license version for the available images. Check the original photo pages and applicable license terms before creating a redistributable dataset or uploading images to an external training service; metadata presence and a passed check are not a legal determination. Check identity, condition and image quality, and preserve attribution. Training exports must keep using the project’s existing explicit acceptance gate; rejected, injured, reference-only, supplemental and unreviewed images are not silently promoted.

[Study-source candidates](pilot_study_candidates.json) record possible provenance for pilot venom profiles and explicitly preserve uncertainty. The original workbook does not identify a primary citation in each source row. The [black mamba follow-up](research_updates/black_mamba_source_review.md) documents a newer 2025 primary study separately, with its methods and pooled-sample context. The black mamba candidate includes a **source-label conflict**: a 2017 review lists 2.9% under natriuretic peptides while its cited 2015 source labels the same 2.9% as non-protein components. The original workbook does not identify its source for the row, so direct provenance is not proved. The original value is preserved in SQLite but [quality flags](../config/venom_quality_flags.json) exclude it from the interface's inputs and matching, the exploratory baseline and the length experiment. The probable boomslang transcriptomic location mismatch is recorded, not silently overwritten.

## First trained experiment

The [length experiment](length_experiment/evaluation.json) tests whether 12 broad venom categories can predict a compilation-reported **species maximum total length**, a coarse proxy for size. The one recorded length is a reported species maximum, not the length of a snake whose venom was measured. A ridge regression was fitted to 267 eligible venom profiles from 141 source species labels. Five-fold evaluation held out whole source genera; predictions were averaged across each held-out species before scoring. The model's mean absolute error was **718 mm**, versus **595 mm** for predicting the training-fold median length. The model performed worse than this simple baseline and is not used by the product.

The experiment keeps each taxonomic genus together across each split, fits imputation and scaling only on training folds, and uses missingness indicators; imputed values are not evidence of absent toxins. Source taxonomy, matching specimens and per-row primary citations remain unverified, and variation in study methods and relatedness may confound the result. These scores are not an estimate of image-generation quality or evidence that venom determines body size. Held-out predictions, input records, hashes, versions and a numeric (not pickle) model artifact are saved in `length_experiment/`. The separate 2025 black mamba candidate is not part of the experiment. To rerun locally with Python, NumPy and scikit-learn installed:

```sh
python3 scripts/train_length_experiment.py
python3 -m unittest discover -s tests -p 'test_length_experiment.py'
```

## Follow-up collection and screening

The [follow-up collection](followup_collection.json) adds 50 photos across the same five species, each from an observation absent from the pre-existing collection. They include 12 cobra, 2 coastal taipan, 12 black mamba, 12 western diamondback and 12 boomslang images. The bounded iNaturalist search found only eight research-grade observations meeting its CC0/CC BY filter for coastal taipan, of which two yielded new qualifying photos; this is not a claim about the total number of available photos across all sources.

A [visual screen](followup_screening.json) rejected six photos, flagged 18 for closer review, and found 26 candidates without an obvious issue at contact-sheet scale. These are screening categories, not confirmed IDs, condition diagnoses or training approvals. All 50 follow-up photos remain excluded from training; their manifests retain photo IDs, observation pages, attribution, license codes and checksums. Observation IDs are not proof of different individual snakes, and two boomslang observations may show the same scene. Exact photo license versions are not recorded by this API; verify them and usage terms before redistribution or external training.

## First baseline

`scripts/run_ml_retrieval_baseline.py` records the earlier reference-comparison method over eligible pilot references: rank by the number of reported categories shared with the query, then by mean absolute percentage-point difference across those categories. The current interface uses a newer coverage-and-distance score and retains all eligible source labels; see the interface README. Unreported entries stay missing, not zero. The historical baseline excludes the query row itself, but cannot guarantee separate studies, individuals or locations because per-profile primary citations and specimen links are not established. The sample result `example_baseline.json` is only a reproducibility example: **it is not an accuracy score, a valid generalization test, or a trained model.**

From the repository root:

```sh
python3 scripts/build_ml_pilot.py
python3 scripts/run_ml_retrieval_baseline.py --query-profile vd2023_e2d1aa974518_r189
python3 -m unittest discover -s tests -p 'test_ml_pilot.py'
python3 -m unittest discover -s tests -p 'test_ml_retrieval_baseline.py'
```

The pilot builder reads the cleaned database and current image manifests, verifies local files against their recorded SHA-256 values, checks recorded license codes/attribution, and retains review states. It produces a database hash so the baseline can detect stale pilot data. It does not create or edit acceptance decisions. To rebuild the underlying species catalog and rendering export after review decisions change, run `python3 scripts/export_rendering_manifest.py` and `python3 scripts/build_species_catalog.py` before rebuilding the pilot.

## Before training an image-based generator

1. Confirm photo identities, health, license details and attribution; expand the accepted set beyond eight source species and the current small observation counts.
2. Resolve source names and aliases, record individual study and sampling provenance when it can be found, and keep unreported toxin categories as missing.
3. Define the task and evaluation. Use observation-level grouping and content hashes so views from the same observation or duplicate files do not leak between image splits. For claims about unseen species, hold out entire reconciled species (and consider related taxa), not just images. With unknown venom study provenance, even species-level comparisons need careful interpretation.
4. Compare any learned approach to this baseline and report coverage, limitations and uncertainty. The current small pilot is for pipeline development, not a convincing species-held-out evaluation or a credible generative model.

## Local computer and Colab

Use the local computer for audits, lightweight CPU baselines, code and tests. Google Colab can run the same version-controlled pipeline and provide a GPU when image-model experiments justify one. GPU availability, session limits and runtime durations vary; save checkpoints and outputs outside the ephemeral runtime. See [Google Colab's FAQ](https://research.google.com/colaboratory/faq.html).

Raw pilot photos are intentionally excluded from Git. Cloning this repository in Colab therefore does **not** supply them: provide only permitted files and their attribution/manifest separately after checking license terms. Paths and checksums need to be checked in the environment that actually runs an image experiment. Uploading or moving material to Colab does not make the photographs specimen-matched with the venom measurements.

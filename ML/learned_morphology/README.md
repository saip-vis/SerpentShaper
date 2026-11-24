# Image-derived direct morphology model: preparation

The intended path is **venom values → trained continuous visual controls → SVG**. It does not select or rank a species at inference. Its training examples associate an image-derived visual annotation with proteomic profiles by source species label; the photos and the venom samples are not known to belong to the same individuals. Species labels are used for joining and grouped evaluation, not as user inputs or model features. This can support exploratory visualization only, not establish that venom determines morphology.

## Current status

`python3 scripts/build_learned_training_data.py` produces `training_data.json` and reports current counts. The current collection contains 1,213 image records. Only 25 satisfy the existing accepted-and-not-excluded source gate; they cover eight source labels. **No numeric image-derived renderer-control annotations have been approved for training**, so the morphology join currently contains zero labeled training images and zero trainable control outputs. An accepted photo alone is not an approved trait label. The separate exploratory color experiment below has measured pixels, but does not supply these renderer-control annotations.

The audit includes `candidate_images`, a triage queue for the already accepted photos. Ten currently have no known review blocks, but that is **not** an automatic approval of any trait annotation: visibility for each trait, identity, condition, and intended usage still need to be assessed. The existing provisional image-trait records and the previously held-out image observations remain excluded. Unreviewed photos are not automatically promoted. This queue can be used to prioritize assistant-supported review rather than asking someone to inspect every one of the 1,213 photos manually.

`python3 scripts/train_learned_morphology.py` writes `readiness.json`. `python3 scripts/train_learned_morphology.py --train` attempts training only if the necessary image-derived labels exist for every output. With today's data it exits with a clear message and writes no model. `MainInterface/trained-model.js` explicitly states `not_trained`.

## Label and evidence contract

`annotations.json` is intentionally empty until there are eligible numeric observations. Each reviewed record must include an existing `image_id`, the matching `species_label`, `review_status: "approved"`, `training_eligible: true`, `annotation_source: "observed_photo"`, a `review_note`, a `traits` object, and a `trait_evidence` string for each provided trait. Supported outputs are defined in `scripts/build_learned_training_data.py` and include eight shared shape/pattern controls plus RGB channels for four color groups. Each value is normalized between 0 and 1. Include only traits supported by the visible part of that image: a hidden tail, a ventral surface not photographed, or a hood not displayed must remain absent rather than be labeled zero. `trait_evidence` should document the visible region/view and the method used to translate it into that shared control. These controls are artistic dimensions; mapping a photograph into them requires a documented geometric fitting or annotation method, not treating a source-species preset as an image measurement.

The builder checks the original manifest's acceptance/exclusion state, image hash, source label, recorded license/attribution and observation ID. It rejects provisional labels and their observation groups, held-out photo observations, duplicate/ambiguous image IDs, conflicting species labels for identical content, and unresolved flagged-quality cases. It never modifies those decisions. `quality_resolution`, when applicable, must document the separate resolution of a flagged issue. The collected CC license codes do not supply all license versions; check the original terms before redistributing or moving photos to a third-party service.

## Candidate training and evaluation

After eligible labels exist, the candidate trainer uses a separate regularized regression for each control. A missing feature is imputed using training-fold medians with missingness information. Zero and blank controls are inactive at inference, with a one-percentage-point activation ramp to avoid a numerical jump as a slider approaches zero. At least three positive inputs are required. Each source species receives equal total training weight, and validation holds out whole source genera; per-control mean absolute error is reported against a training-fold mean baseline. This grouping prevents photos or profiles of the same genus from appearing in both sides of a fold, though it does not resolve broad taxonomic relatedness, provenance, geographic variation, or limited sample size.

The workflow currently requires at least four source species across three genera for **each** control merely to run a grouped experiment. Those engineering minimums are not enough to establish biological validity or reliable generation. An actual fit produces an `experimental_candidate_not_for_product` artifact. It is not automatically exposed to end users; evidence quality, actual model performance, and the behavior of both surfaces still require evaluation. No such artifact exists now.

## Photo-patch color pilot and image triage

Nine manually located body patches in accepted, unblocked images are recorded in `body_patch_samples.json`. `extract_body_patch_pilot.py` verifies the source review gate and image hashes, then measures the median sRGB of each small crop in `body_patch_measurements.json`. These are patch colors, not verified colors of the whole animal; lighting, camera processing and markings affect them. They include nine distinct observations across eight source species. Venom profiles are joined by source label, not matched individuals; the five newly reviewed photos retain provider-assigned species identities that were not independently verified. One earlier patch was removed after its observation was held due to an unresolved tail condition; the user’s identification review and source files are preserved.

`train_photo_color_pilot.py` trains three direct venom-to-patch-color ridge regressions with no species feature at inference. In the tiny leave-one-genus-out check, mean absolute error across color channels was about 35.3 on the 0–255 scale, versus 33.2 for the training-species mean baseline. Eight held-out species are far too few for a robust conclusion. An earlier experiment used grouped folds that could hold out more than one genus at a time; the evaluator now explicitly holds out one entire genus per fold. The resulting `body_patch_color_experiment.json` is exploratory. Its coefficients are reused for a 15% skin-color cue in the connected prototype; it does not predict head shape, body shape, full-snake color, or a ventral view.

## Exploratory geometry from photos

`photo_geometry_annotations.json` records manually placed, normalized landmarks on four accepted photos from four source species. Two examples measure projected head height divided by projected head length in side-oblique photos; two measure the projected spacing between visible repeated body markings relative to local projected body width. `measure_photo_geometry.py` validates the source gate and file hash, then computes the ratios using image pixel dimensions and records the evidence in `photo_geometry_measurements.json`. The coordinates are reviewable and the optional overlays show where they were placed. They do not establish actual anatomical dimensions, and a side-view head height is not dorsal head width. Perspective, pose and occlusion differ across photos.

These examples demonstrate a repeatable measurement method; they are not approved renderer-control labels, do not cover all required traits, and do not train or enable the renderer model. To inspect locally, run `python3 scripts/measure_photo_geometry.py --overlay-dir /private/tmp/serpentshaper_geometry_overlays` in a Python environment with Pillow and the original photos. Do not commit or redistribute the derived photo overlays without checking the source licenses.

`image_triage_batch_001.json` and `image_triage_screen_001.json` record an initial contact-sheet screen of 72 photos from 24 source labels. Six severely damaged specimens were individually inspected and rejected in the original manifests. Five further photos were individually inspected and accepted, with evidence restricted to visible areas; the remaining 61 remain unreviewed. Thumbnail-level review does not establish identity, health or suitability for a particular trait. `build_image_triage_queue.py` prepares a fresh batch, keeping accepted and rejected images and previously protected observation groups out of the queue. It does not make review decisions.

The extraction requires Pillow; the color trainer requires NumPy and scikit-learn. For example:

```sh
python3 scripts/build_image_triage_queue.py
python3 scripts/render_image_triage_sheets.py
python3 scripts/extract_body_patch_pilot.py
python3 scripts/train_photo_color_pilot.py
```

Raw images remain local and are required to re-run these steps. The outputs preserve source links, recorded attribution, crop coordinates and image hashes; license terms still need review before redistributing source photographs or uploading them to another service.

## Interface and testing

The main `MainInterface/index.html` has an **experimental hybrid**: direct venom-to-control learning from authored designs, plus a small photo-patch-derived color cue. Its detailed procedural rendering interpolates shared geometry and motifs from those controls; it is not the image-derived morphology model specified above. Users can load one reported profile for any of 149 source species and see that species' reference illustration separately. Changing venom inputs changes the generated concept independently of the selected reference. The earlier `MainInterface/learned-preview.html` remains a gated placeholder specifically for the future image-derived morphology model. The reference-based research interface is preserved at `MainInterface/research-interface.html`. Dorsal and ventral concepts share a body shape; the ventral drawing is not a 3D reconstruction and needs its own image evidence.

Run:

```sh
python3 scripts/build_learned_training_data.py
python3 scripts/train_learned_morphology.py
python3 -m unittest discover -s tests -p 'test_learned_morphology.py'
node --test MainInterface/learned-inference.test.cjs
```

The morphology tests use synthetic data to check model mathematics, review gates, grouped evaluation, browser/Python inference parity, zero-input continuity and the preview. Passing them does not validate a full-snake model.

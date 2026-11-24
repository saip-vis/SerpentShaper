# Pilot review findings

## What was reviewed

The five pilot contact sheets were visually triaged; several questionable photos were inspected individually at larger size. This is a preliminary suitability review, not expert species identification or a complete anatomical survey. Per-image flags are in `pilot_image_review.json` and current provider metadata are in `pilot_metadata_snapshot.json`. The existing acceptance status and exclusions remain the machine-readable training gate; advisory image-quality flags do not automatically clear a photo for every ML task.

## Changes made

- **Coastal taipan, TA07–TA10:** Four views belong to observation 347294159. The full-body views show severe body damage. All four were rejected and excluded from training under the user's healthy-phenotype rule. Existing files and earlier review provenance remain intact.
- **Coastal taipan, TA01 and TA04:** These are visually the same scene, with different photo/observation IDs and different file hashes. Their decoded images have the same dimensions and mean absolute RGB differences under one intensity value per channel. The current iNaturalist API identifies the same observer and observed date for both observations. TA04 is held out as a near duplicate; TA01 remains accepted. Never place near-duplicate content across train and test, even when observation IDs differ.
- **Black mamba:** BM01 has a hand around the animal's neck, while BM05–BM07 are significantly obscured by foliage. They remain accepted based on the prior user review but are flagged for a task-specific decision before full-image training. BM09 and BM10 are partial views from one observation, not independent individuals.
- **Western diamondback:** WD04 is letterboxed with a small subject; WD05 is dark and obscured. These remain accepted but have quality flags for the intended task. WD06–WD07 and WD09–WD10 are paired views of individual observations.
- **Boomslang:** BO07 and BO08 are head close-ups and their provider descriptions identify juveniles, so they should not silently represent full adult morphology. BO02 and BO10 were already rejected. Other unreviewed photos remain unreviewed.
- **Spectacled cobra:** SC07 is the photograph the user previously questioned; the current provider label is *Naja naja*, but this review does not independently settle the identity. SC08–SC09 show only a small portion of the animal, and SC10 has a dark area whose condition is uncertain. Their unreviewed state is unchanged.

There are now **22 accepted, metadata-checked records from 16 observation groups** among three pilot species: 5 coastal taipan, 7 black mamba and 10 western diamondback. Some accepted photos have additional quality flags and should not be interpreted as a final 22-image training set.

## Licensing

The iNaturalist observation API returned all 36 requested observations and all 50 photos in the pilot, and the current per-photo license codes matched the stored codes. All 50 carry provider labels marked research-grade, including recognized subspecies of *D. typus*; this is community metadata, not independent verification of anatomy or a guarantee of photo quality. The API snapshot does not contain an exact license version for the photos. Direct photo pages returned HTTP 403 in this environment, so exact version and original provenance could not be independently confirmed. Do not infer the version from the code; retain photographer, photo URL, code, retrieval date and attribution and check the individual photo pages before redistribution or external training.

Source: https://help.inaturalist.org/en/support/solutions/articles/151000169918-can-i-use-the-photos-and-sounds-that-are-posted-on-inaturalist-

## Venom source provenance

The 2023 dataset paper states that its venom data were compiled from 164 studies. The original workbook's `RAW_DATABASE_VENOM` sheet contains species, location, measurement type and composition, but no row-level citation column; no cell comments or hyperlinks were found in that sheet. Species names and toxin values by themselves are not enough to assign provenance definitively.

Four plausible study candidates were found by comparing selected pilot profile values with a separate proteome compilation and accessible papers. They are explicitly marked as candidate matches in `pilot_study_candidates.json`; none has been inserted as a confirmed citation in the cleaned database. The second western diamondback, Australian coastal taipan and boomslang profiles have no confirmed individual source, and one apparent Australian taipan match has conflicting values. The black mamba candidate study describes pooled venom, demonstrating why it is unsafe to pair that profile with an unrelated photograph as if both came from one snake.

## Next steps before training

- Review task-specific visibility flags, and collect more clearly licensed, healthy photographs from additional observation groups. Prioritize the categories and anatomical views needed for the intended generative output.
- Check photo license versions, attribution and original sources at their photo pages; keep CC BY and CC0 conditions separate and do not treat current metadata as legal advice.
- Verify candidate source-study mappings against original articles and explicitly record sample pooling and provenance. Do not fill missing citation IDs based on species name or numerical similarity alone.
- Keep related observation groups and duplicate or near-duplicate images together during splitting; reserve species-held-out evaluation for claims about unseen species. No training or accuracy evaluation has been performed in this review.

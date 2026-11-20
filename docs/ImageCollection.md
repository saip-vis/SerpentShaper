# Image collection pilot

This is a small, bounded iNaturalist collector for testing our image manifest and review workflow. No model is trained. It uses public API metadata instead of parsing web pages. Use [provider exports or licensed datasets](https://www.inaturalist.org/pages/developers) for bulk acquisition; this command intentionally permits one species per folder and examines at most 50 observations per species in one batch.

## Run the default pilot

Python 3 is sufficient; there are no extra packages or API keys. From Terminal:

```bash
cd /Users/saipranavviswanathan/SerpentShaper
python3 scripts/collect_image_pilot.py discover
```

The default is Naja naja in `pilot_001_spectacled_cobra`. The collector searches exact documented names, checks taxonomic ancestry, requests research-grade observations, and independently checks every photo's license, attribution, visibility flags, and original dimensions. It accepts CC0/CC BY candidates with both dimensions at least 512 pixels. Observation quality grade is not image-quality verification. Never use the taxon's default photo as an observation photograph.

New discovery runs select one candidate from each observation before taking additional views, with a default maximum of two photos per observation (`--max-per-observation 2`). This reduces concentration in one encounter; it does not establish distinct individuals or remove photos from an existing manifest. All photos of one observation still share a split group. Original six batches retain their historical selection.

Assistant suitability screening uses `candidate`, `supplemental`, or `rejected`. A candidate is a possible primary visual reference; supplemental images may show useful anatomy under handling, partial views, or special poses. Neither category constitutes expert species verification or final training acceptance.

## Healthy phenotype policy

The user's review rule is recorded in `config/image_review_policy.json`: exclude injured, damaged, or deformed snakes from the rendering dataset. If an image contains uniquely useful anatomy unavailable in healthy alternatives, retain it only as a documented reference exception, separate from rendering-training examples. No such exception has been approved so far. Uncertain condition is held out pending review; unusual color or posture alone does not establish injury. Reject substantial hand occlusion when clearer alternatives already cover the anatomy.

Run `python3 scripts/export_rendering_manifest.py` to write `data/image_pilots/rendering_manifest.json`. It includes only explicitly accepted downloaded records and excludes rejected/supplemental suitability categories, rendering exclusions, and reference-only exceptions, even if a conflicting accepted status is present. Original files remain for provenance; trainers should consume this filtered manifest rather than globbing every image folder. This is an export gate, not a model-training implementation or a guarantee of model output quality.

## Remaining 140 species: sampled acquisition run

`scripts/download_remaining_species.py` freezes a plan excluding the original nine species and creates one Latin-name folder per remaining label, numbered 010–149. It runs the bounded collector sequentially: at most 20 observations, 10 photo candidates, and two photos per observation per species. It is a sample of each provider taxon, not an exhaustive species download. Exact original/alternative name matching remains mandatory. The program needs Pillow to generate review pages/contact sheets; use the bundled Python runtime where available.

The run saves `plan.json`, `progress.json`, and `post_download_notes.md` under `reports/image_research/remaining_species_downloads/`. Each attempted species is recorded, including zero-result searches, taxonomy mismatches, failed metadata requests, filtered-out samples, partial downloads, and download errors. The filter diagnostics count overlapping rejection conditions, so they must not be added as distinct rejected-photo counts. Each folder keeps its own cache, collection log, discovery summary, manifest, and review page if downloads succeed.

Re-running the same command skips recorded completed species. The process saves after each species; if interrupted during a species, downloads already in its manifest are checksum-verified and skipped on resumption. A recorded failure is retained for follow-up rather than retried indefinitely. A 429/403 provider response stops further collection. A different provider or changed species mapping requires a separately documented follow-up; a skipped sample does not prove global photo absence.

All new records explicitly set `rendering_training_excluded: true` with reason `pending_visual_review`. Accepting a reviewed record later must also clear that pending exclusion; injury exclusions and reference-only exceptions must remain excluded. There is no automated injury or species classifier in this collector. Original nine species folders are unchanged by this run.

The completed run attempted all 140 remaining source labels: 91 reached 10 downloaded records, 37 yielded partial batches, 11 had no observations matching the license/quality query, and one name was unresolved. There are 1,073 new records containing 1,063 distinct image contents. The ten duplicate pairs come from the Cryptelytrops/Trimeresurus purpureomaculatus name pair. Both original source labels remain traceable; later duplicate copies have `duplicate_of` references and cannot enter the rendering export.

Open `data/image_pilots/index.html` for the searchable species index. Full outcomes and the 12 skipped labels are in `reports/image_research/remaining_species_downloads/post_download_notes.md`. `verification.json` contains checksum/path/resolution/quarantine checks and duplicate groups. Run `scripts/validate_image_collection.py` with Pillow available to reproduce that audit. One unusually large original is flagged for bounded-resolution preprocessing before model ingestion; original files are preserved.

The current species folders under `data/image_pilots/` are:

- `pilot_001_spectacled_cobra/`: Naja naja, 10 downloaded images.
- `pilot_002_coastal_taipan/`: Oxyuranus scutellatus, 10 downloaded images.
- `pilot_003_black_mamba/`: Dendroaspis polylepis, 10 downloaded images, including three rejected documents/collages retained for provenance.
- `pilot_004_western_diamondback/`: Crotalus atrox, 10 downloaded candidates.
- `pilot_005_puff_adder/`: Bitis arietans, 10 downloaded files, including two rejected text documents retained for provenance.
- `pilot_006_jararaca/`: Bothrops jararaca, 10 downloaded candidates.
- `pilot_007_boomslang/`: Dispholidus typus, 10 downloaded files; one visibly wounded specimen rejected from typical phenotype references.
- `pilot_008_olive_sea_snake/`: Aipysurus laevis, 10 downloaded files; one blurry image rejected.
- `pilot_009_gaboon_viper/`: Bitis gabonica, 10 downloaded files; two damaged specimens rejected.

Each has its own `manifest.json`, `images/`, `review.html`, and contact sheet. The original mixed-species pilot folders are preserved in `_archive/` and are not the active review folders. Numbers are organizational IDs, not biological categories. Species names determine folder contents.

Default outputs appear under `data/image_pilots/pilot_001_spectacled_cobra/`:

- `manifest.json`: photo and observation IDs, species mapping, source pages, attribution, license code, dimensions, and review fields.
- `discovery_summary.json`: per-species results and errors. Zero selected candidates is a valid result, not proof images do not exist.
- `api_cache/`: dated provider responses. Identical requests reuse these snapshots; choose a new batch to refresh.

Discovery downloads metadata only. Download at most 10 candidate photos with:

```bash
python3 scripts/collect_image_pilot.py download --limit 10
```

Images are stored in `images/` with SHA-256 filenames. Identical bytes share a file; re-runs verify downloaded checksums before skipping. Photo attribution remains in each manifest entry. Similar crops or resized copies still need perceptual duplicate review. The downloader limits individual files to 20MB and checks response type; downloaded candidates still require visual/file review.

## Choose a species or a separate batch

```bash
python3 scripts/collect_image_pilot.py discover --batch gap_check_001 \
  --species "Atropoides picadoi" --limit 10
python3 scripts/collect_image_pilot.py download --batch gap_check_001 --limit 5
```

Species must match source labels in `reports/image_research/imaging_gaps.json`. Documented alternative names are used for searches while original venom labels remain intact. Unresolved names are reported rather than guessed. This first collector covers iNaturalist only; it does not resolve missing species from Commons, museums, or other websites yet.

## Review before using photos

Every candidate starts as `unreviewed`; framing, viewpoint, and pose start as `unknown`. Inspect the original source page and image to confirm identity, license terms, body/head visibility, blur, occlusion, and multiple animals. Record `accepted` or `rejected` in `review_status`, and fill the annotation fields. The API license code does not identify a version, so `license_version` is explicitly unknown until checked; do not infer CC BY 4.0 from that code. Downloading does not automatically accept a photo for training.

Keep all photographs from an observation together using `split_group`. These are species-level references, not photographs of the individual snakes whose venom was measured. SnakeCLEF and iNaturalist overlap, so their records must not be counted as independent sources.

Requests are sequential, cached, and spaced by at least 1.2 seconds. Failed requests are recorded; there is no automatic retry loop. API responses can include public observation information not copied into the manifest. Review cached responses before sharing. Large media and API caches are ignored by Git.

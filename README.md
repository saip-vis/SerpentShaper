# SerpentShaper

Biologically informed visualization of hypothetical snakes from user-defined venom profiles.

This folder contains the venom data pipeline, image references, procedural renderer and experimental trained models. The connected prototype learns shape from authored snake designs associated with venom by source species label, with a small color cue trained on photo patches. Venom and photographs are not matched by individual snake; the output is not validated as a biological predictor.

Start with [the dataset report](reports/dataset_report.md).

For ingestion, see [the cleaning report](reports/cleaning_report.md). The SQLite database and flat tables are in `data/processed/venom_diet_2023/`.

The [homepage](MainInterface/home.html) introduces the project and links to the [venom explorer](MainInterface/index.html), which connects venom-family inputs directly to a trained experimental SVG concept and explains the model's responses. The homepage's king cobra image is an AI-generated illustration, not a source photograph. See [usage and limitations](MainInterface/README.md) and the [connected model's training report](ML/learned_morphology/connected_prototype.json). The earlier, more detailed reference-based renderer is preserved in the [research interface](MainInterface/research-interface.html).

To run the main interface with local PDF/text study search, run `./start_serpentshaper.sh` and open `http://127.0.0.1:8768/`. Study passages and optional literal-percentage suggestions remain local; users review and apply values explicitly. Optional retrieval-augmented answers use a separately installed local Ollama `llama3:latest` model and do not retrain the phenotype model. See the interface notes for limitations and dependencies.

### Render static deployment

`render.yaml` configures the public website as a Render static site. Connect this repository on Render, or create a static site from `main` with build command `python3 scripts/build_render_site.py` and publish directory `render-dist`. The build copies only the pages and assets needed for the website; it does not publish the raw research data, local photos, or the study server. The trained generator runs in the visitor's browser and needs no API key. Study uploads and local-AI answers are available only through the local server, not the public static site. The local server is not designed to be exposed to the internet. The 50% input minimum is an interface rule, not a validated accuracy threshold.

To browse the cleaned data and test custom inputs locally, run `python3 InitialInterfaceTest.py` and open `http://127.0.0.1:8765`. See [interface usage and API](InitialInterfaceTest.md).

The [venom input specification](docs/VenomInputSpecification.md) defines four primary and eight advanced controls available in the composition editor. Its biological phenotype output contract remains a draft; the connected model produces an experimental illustration rather than validated phenotype inference. Validate the catalog's database bindings with `python3 scripts/validate_input_spec.py`.

For the first image collection batch, see [the image pilot instructions](docs/ImageCollection.md). Run `python3 scripts/collect_image_pilot.py discover` to collect a small licensed-photo candidate manifest, then `python3 scripts/collect_image_pilot.py download --limit 10` to download candidates separately. Images remain unreviewed until inspected; use provider exports for bulk acquisition.

To curate the downloaded candidates, run **`./start_image_review.sh`** and open **http://127.0.0.1:8767**. The [image review interface](docs/ImageReviewInterface.md) saves accept/reject/flag/reference decisions and anatomy labels directly to manifests, provides bounded previews, backups and undo, and refreshes the filtered rendering export after every save.

The [image review policy](config/image_review_policy.json) excludes injury/deformity examples from rendering training and keeps any documented unique-anatomy exceptions reference-only. Run `python3 scripts/export_rendering_manifest.py` to export explicitly accepted, non-excluded records for later ingestion; original download folders also contain rejected and pending files.

## Contents

- `data/raw/`: unmodified downloaded data files and original supplementary archives.
- `sources/`: repository metadata, dataset metadata, open-access article XML, download URLs, timestamps, and SHA-256 checksums.
- `reports/dataset_report.md`: recommendations, coverage, limitations, and next steps.
- `reports/data_audit.json`: measured file counts and detailed audit results.
- `sources/dataset_registry.json`: machine-readable source register.
- `scripts/`: acquisition scripts and the reproducible, read-only audit.

Run the audit with `python3 scripts/audit_sources.py` from this folder. It reads the downloaded files and writes the JSON audit. The download scripts make network requests; they are retained for provenance and are not needed to read the data.

Original files remain unchanged. The processed workbook tables preserve source values and separate records requiring review. Experimental models use derived species-level associations; their outputs do not modify the source data.

For species-level venom/image links, run `python3 scripts/build_species_catalog.py`. See [the species catalog guide](docs/SpeciesCatalog.md) for the JSON structure, coverage and limitations.

For physical characteristics across the species catalog, see [physical reference profiles](docs/PhysicalProfiles.md) and the [complete species outline](docs/physical_profiles/AllSpeciesPhysicalProfiles.md). Rebuild the JSON export with `python3 scripts/build_physical_profiles.py`.

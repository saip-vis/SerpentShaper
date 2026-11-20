# SerpentShaper

Biologically informed visualization of hypothetical snakes from user-defined venom profiles.

This folder contains dataset discovery, an initial source audit, and a cleaning pipeline for the 2023 venom workbook. It does not contain a trained model or a merged training dataset.

Start with [the dataset report](reports/dataset_report.md).

For ingestion, see [the cleaning report](reports/cleaning_report.md). The SQLite database and flat tables are in `data/processed/venom_diet_2023/`.

To browse the cleaned data and test custom inputs locally, run `python3 InitialInterfaceTest.py` and open `http://127.0.0.1:8765`. See [interface usage and API](InitialInterfaceTest.md).

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

Original files remain unchanged. The processed workbook tables preserve source values and separate records requiring review. They have not been normalized, merged with other sources, or analyzed with ML or correlations.

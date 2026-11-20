# Species catalog

Rebuild from the repository root:

```sh
python3 scripts/build_species_catalog.py
```

The engine entry point is `data/processed/species_catalog/catalog.json`. A compact coverage report is in `reports/species_catalog_summary.json`. Rebuild after collecting images or saving reviews; this export is a snapshot, not a live database.

## Reading the catalog

- `species`: one entry per normalized source label, with a stable `species_id`, original name, lookup alias and reference, observed provider taxon IDs, profile IDs, image records, counts, and collection notes.
- `profiles`: original venom profile metadata plus `reported_components`, joined through `venom_profile_ids`. Each component retains its toxin ID, value status, source cell and raw value. `toxin_dictionary` supplies the category labels. Missing component rows are omitted and must not be interpreted as zero. No averaging or normalization is performed. Proteomics and transcriptomics remain separate, and held profiles retain their ingestion status.
- `images`: original manifest fields including attribution, license, observation group, checksums and review/exclusion flags, plus repository-relative paths, a file-availability check, species-link status and `rendering_eligible`. Refer to `manifest_path` for the authoritative review record. File availability checks existence, not image integrity or a new visual assessment.
- `inputs`: SHA-256 fingerprints of the database, manifests and mapping reports used to build the snapshot.

Images are associated with species, not with the individuals or populations sampled for venom. This catalog does not establish a relationship between venom and visible traits. Shared provider taxon IDs are recorded without merging source labels; repeated hashes and observation IDs remain available to prevent duplicate counting and future split leakage. Family, diet, habitat and morphology are not inferred from species names.

## Current coverage

The complete venom database has 174 source labels and 356 profiles. The earlier image campaign targeted 149 labels, of which 137 have photos. Including the 25 labels outside that campaign, 37 catalog labels lack photos. Missing-photo entries retain collection skip notes when available; absence outside the campaign means not collected, rather than a failed search.

There are 1,163 image records representing 1,153 distinct content hashes. All files were available at build time. Ten records currently meet the existing rendering export policy. The remaining records are retained for exploration with their existing flags; catalog construction does not approve or reject any photo. Manual review can remain paused.

## Example lookup

```python
import json
from pathlib import Path

catalog = json.loads(Path('data/processed/species_catalog/catalog.json').read_text())
species = next(s for s in catalog['species'] if s['source_species_name'] == 'Naja naja')
profiles = {p['profile_id']: p for p in catalog['profiles']}
venom = [profiles[pid] for pid in species['venom_profile_ids']]
photos = [i for i in species['images'] if i['file_available']]
# For a future rendering dataset, also require rendering_eligible.
```

This is a data integration step. No model is trained and no phenotype is generated.

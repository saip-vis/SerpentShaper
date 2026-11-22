# InitialInterfaceTest

A local browser interface and JSON API over the cleaned 2023 venom database. No extra Python packages are required.

## Start

```sh
cd /Users/saipranavviswanathan/SerpentShaper
python3 InitialInterfaceTest.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Stop with Ctrl+C. Use `--port 8766` if the default port is occupied. Paths are resolved relative to the Python file, so it also works from another working directory.

## Browser interface

- Browse profiles by species or location, with separate proteomics and transcriptomics filters.
- Held profiles are hidden by default. The checkbox allows explicit inspection, with review flags shown.
- View all source ingredient labels and percentages; missing and invalid entries can be revealed separately.
- Inspect dataset DOI, source row and cell locations, import notes, and the engine JSON.
- Download an individual profile as JSON.
- Build a composition using four primary controls (3FTx, PLA2, SVMP, SVSP), plus eight expandable advanced controls.
- Each control includes a percentage field, slider, definition, category boundaries, and linked evidence notes.
- See assigned, unallocated, and overallocated percentages update immediately. Values are never rescaled automatically.
- Use an eligible proteomic profile as a starting point. All 130 source entries remain attached, including missing entries; the 118 categories outside the control catalog are read-only and visible in a separate panel. Transcriptomic and held profiles remain inspectable but cannot seed this editor.
- Download validated draft compositions as JSON. Drafts are held only in the browser session; no changes are written to the database.

The Python entry point serves `InitialInterfaceTest.html` from the same project folder. Keep both files together. Controls and help text come from `config/venom_input_spec.json` and `evidence/input_evidence.json`, not duplicated scientific labels in the frontend.

The custom validator checks known source IDs, unique entries, finite percentages from 0 to 100, nonblank entries, and a total of 100% ±0.01 percentage points. This custom-input rule is deliberately stricter than the cleaning pipeline's 95–105% review range for historical measurements. No input is automatically normalized. Omitted components are unspecified; an explicit zero remains zero. Unknown terminology produces a warning, not an invented biological interpretation.

## JSON API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/summary` | Dataset counts, source metadata, and read-only status |
| GET | `/api/toxins` | All 130 source labels and available standardized names |
| GET | `/api/input-spec` | Bound control catalog and evidence notes with source links |
| GET | `/api/profiles` | Search/filter/paginate profiles |
| GET | `/api/profiles/PROFILE_ID` | Full composition, source, and import notes |
| POST | `/api/validate` | Validate a custom composition without saving it |

Profile-list query parameters: `q`, `measurement_type` (`proteomics`, `transcriptomics`, or `unknown`), `include_held=1`, `limit` (1–100), and `offset` (nonnegative). Profile detail also requires `include_held=1` to inspect held records.

Example validation request:

```json
{
  "components": [
    {"toxin_id": "vd2023_E", "abundance_pct": 60},
    {"toxin_id": "vd2023_T", "abundance_pct": 40}
  ]
}
```

Send with `Content-Type: application/json`. Invalid composition content returns HTTP 200 with `valid: false` and explanatory errors. Malformed requests return HTTP 400; missing profiles return 404; held profiles without explicit opt-in return 403.

### Editing a measured profile without dropping categories

Supply `source_profile_id` together with an array of edits to catalog-bound controls. An empty edit array preserves the complete original profile. Example:

```json
{
  "source_profile_id": "vd2023_e2d1aa974518_r2",
  "components": [
    {"toxin_id": "vd2023_T", "abundance_pct": 41},
    {"toxin_id": "vd2023_AZ", "abundance_pct": 25.5}
  ]
}
```

The server reloads the eligible source profile itself and retains every other component, rather than trusting the browser to send a complete source composition. It returns all 130 entries with source cell, original value, provenance, and `origin` (`source` or `user_edit`). Source-only edits are rejected. Inherited missing values stay NULL and produce a summary note; explicitly clearing a control value is an unresolved edit and fails complete-input validation. All edited compositions are marked `user_defined`, with `source_context` identifying their measured starting point.

This example adjusts PLA2 from 42 to 41 and SVMP from 24.5 to 25.5, retaining the original 100% source-column sum. Original unreported categories remain unknown; a 100% sum does not prove biological completeness or non-overlap.

The legacy custom-input API without `source_profile_id` still accepts original source toxin IDs, including labels outside the grouped UI, so existing clients remain compatible. The browser's new-composition editor exposes only the 12 defined controls. A source-only category does not become a phenotype-driving input merely because the raw API can retain it.

This server binds only to the local loopback address and opens SQLite in read-only mode. It serves only this interface and its API, not arbitrary project files. It is intended as a local test interface rather than an externally hosted application.

Species names remain unreconciled source labels. Available profiles are structurally eligible with caveats; they are not biologically validated. No analytics, predictions, RAG, image generation, or database writes are performed.

Tests: `python3 -m unittest discover -s tests -v`.

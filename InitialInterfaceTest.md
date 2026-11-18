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
- Copy reported values into the custom input test or enter components yourself. This does not modify the database.

The custom validator checks known source IDs, unique entries, finite percentages from 0 to 100, nonblank entries, and a total of 100% ±0.01 percentage points. This custom-input rule is deliberately stricter than the cleaning pipeline's 95–105% review range for historical measurements. No input is automatically normalized. Omitted components are unspecified; an explicit zero remains zero. Unknown terminology produces a warning, not an invented biological interpretation.

## JSON API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/summary` | Dataset counts, source metadata, and read-only status |
| GET | `/api/toxins` | All 130 source labels and available standardized names |
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

This server binds only to the local loopback address and opens SQLite in read-only mode. It serves only this interface and its API, not arbitrary project files. It is intended as a local test interface rather than an externally hosted application.

Species names remain unreconciled source labels. Available profiles are structurally eligible with caveats; they are not biologically validated. No analytics, predictions, RAG, image generation, or database writes are performed.

Tests: `python3 -m unittest discover -s tests -v`.

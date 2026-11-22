# SerpentShaper venom explorer

Open `MainInterface/index.html` in a browser. The interface is local and uses the checked-in data bundle and the existing procedural SVG renderer; no server or packages are required. Select a measured proteomic profile or clear it to enter a composition. Expand **More families & peptides** for additional source categories. Values are session-only.

Each blank control means unknown or unreported, while an entered zero is explicit. Selecting a measured profile retains all other source categories, including missing values. The reported total includes the editable values and any other reported source categories; the unallocated amount is only an arithmetic balance. Totals are not automatically normalized, and historical source totals can differ slightly from 100%. Family categories are kept distinct and no parent-child aggregation is inferred. The peptide controls are broad source categories, not individual peptide identities.

The reference list compares only the editable categories reported in both the input and each dataset profile. Results are sorted first by the number of shared categories and then by mean absolute percentage-point difference over those categories; the UI displays both coverage and distance. Comparisons with few shared categories are weak, and the same score can describe very different unknown compositions. Source names are joined to illustrations by exact label, not verified taxonomic identity. Held profiles and transcriptomic measurements are excluded. The source DOI is dataset-level; it is not a per-profile primary study citation.

The preview is the selected reference species' illustrative preset. A slider may change which reference is shown; it does not predict anatomy or morph a snake through a trained model. The dorsal and ventral controls alter the displayed surface of the existing single-projection SVG; they are not reconstructed angles. Fine morphology remains illustrative and unvalidated. Study uploads, RAG, individual peptides, ecological inference and machine learning generation are not implemented.

## Rebuild and verify

From the repository root:

```sh
python3 scripts/build_species_presets.py
python3 scripts/build_main_interface_data.py
node MainInterface/matching.test.cjs
```

The builder reads the cleaned SQLite database and checks the toxin-control source binding. It writes `venom-data.js` with 276 eligible proteomic profiles and all source categories. Dataset counts may change when the cleaned database changes. The tests check that missing values are not imputed, source categories are retained, comparisons and totals are correct, and the controller responds to edits.

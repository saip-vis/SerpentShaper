# SerpentShaper venom explorer

Open `MainInterface/index.html` in a browser. The interface is local and uses the checked-in data bundle and the existing procedural SVG renderer; no server or packages are required. Select a measured proteomic profile or clear it to enter a composition. Expand **More families & peptides** for additional source categories. Values are session-only.

Each blank control means unknown or unreported, while an entered zero is explicit. Selecting a measured profile retains all other source categories, including missing values. The reported total includes the editable values and any other reported source categories; the unallocated amount is only an arithmetic balance. Totals are not automatically normalized, and historical source totals can differ slightly from 100%. Family categories are kept distinct and no parent-child aggregation is inferred. The peptide controls are broad source categories, not individual peptide identities.

An uncertain black mamba NP source value is deliberately left blank and excluded from similarity comparisons. Its original value remains in the database and generated component metadata; the [quality flag](../config/venom_quality_flags.json) records why it is withheld. A user may enter their own NP value, but the withheld reference value will not be used for matching.

The reference list compares only the editable categories reported in both the input and each dataset profile. Results are sorted first by the number of shared categories and then by mean absolute percentage-point difference over those categories; the UI displays both coverage and distance. Comparisons with few shared categories are weak, and the same score can describe very different unknown compositions. Source names are joined to illustrations by exact label, not verified taxonomic identity. Held profiles and transcriptomic measurements are excluded. The source DOI is dataset-level; it is not a per-profile primary study citation.

The preview starts from the selected reference species' illustrative preset. When at least three categories have values, an experimental trained regression changes its skin and marking colors, marking spacing, scale detail and body/hood width; the model is trained on the project's authored artistic presets paired by source species label, not on photographs or individual venom samples. The results are imagined concepts, not validated biological predictions. With fewer than three input categories the original reference is shown. The model uses training-set median imputation with explicit missingness indicators; a blank input is not a claim that a toxin is absent.

The base preset still determines the snake's anatomical template and pattern type. Width adjustments are bounded to under 5%, and colors, marking spacing and scale detail are also bounded. Choose a different reference card to change the base. Download SVG saves the displayed concept; **Edit base anatomy** opens the source preset and does not carry over the generated style. Dorsal and ventral controls alter the displayed surface of the existing single-projection SVG; they are not reconstructed angles. Study uploads, RAG, individual peptides and ecological inference are not implemented.

## Rebuild and verify

From the repository root (the training and Python test commands require NumPy and scikit-learn):

```sh
python3 scripts/build_species_presets.py
python3 scripts/build_main_interface_data.py
python3 scripts/train_visual_style_model.py
node --test MainInterface/matching.test.cjs MainInterface/style-inference.test.cjs MainInterface/style-library.test.cjs
python3 -m unittest discover -s tests -p 'test_visual_style_model.py'
```

The data builder reads the cleaned SQLite database and checks the toxin-control source binding. It writes `venom-data.js` with 276 eligible proteomic profiles and all source categories. The visual style trainer writes an inference bundle and [training manifest](../ML/visual_style_model.json) with hashes, source labels, input values, artistic target parameters and limitations. Dataset counts may change when inputs change. The tests check training-to-browser numerical parity, quality exclusions, bounded style and width changes, closed contours, comparisons and controller interactions.

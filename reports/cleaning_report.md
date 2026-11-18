# Venom workbook cleaning

Scope: only `RAW_DATABASE_VENOM` in `data/raw/venom_diet_2023/Supp. Mat. 1.xlsx`. No correlations, predictive models, taxonomy inference, ecological joins, or biological-effect classifications were performed. Original files are unchanged.

## Outputs

All ingestion outputs are in `data/processed/venom_diet_2023/`:

- `serpentshaper.sqlite`: primary ingestion database with foreign keys, numeric constraints, indexes, and filtered views.
- `profiles.csv`: one record per source row, including original and formatted species names, measurement type, location, provenance, validation status, and the original source-row JSON.
- `components.csv`: one record per profile and source ingredient column, including missing cells. Every record retains its source cell address and original value.
- `toxin_dictionary.csv`: all 130 labels, kept distinct. Thirteen familiar labels have explicit standardized names; 117 retain their original labels for review. Named mappings identify labels, not biological functions or validated aggregation rules.
- `profile_exceptions.csv`: only blocking profile issues, with species names and workbook row numbers. Start here to resolve record exceptions.
- `review_queue.csv`: full audit log, including corrections, verified formulas, and dictionary-level review items.
- `summary.json`: counts, checksums, schema version, scope, and limitations.
- `cleaning_rules_snapshot.json`: exact mappings used for this run.

Initial result: **356 profiles retained, 333 structurally ingestible with caveats, 23 held for review**. The eligible subset contains 276 proteomic profiles and 57 transcriptomic profiles, in separate views. This is a validation result, not a scientific reliability score.

## Applied rules

1. Trim whitespace and replace species-name underscores with spaces. Keep original spelling and taxonomic labels; do not guess synonyms, accepted names, common names, or family assignments.
2. Use explicit measurement aliases. Seven `trancriptome` entries map to `transcriptomics`, and trailing whitespace is removed. `unknown` and `proteoje` remain unresolved.
3. Import source columns E:ED only as ingredient measurements. Ignore empty unlabeled column D. Exclude calculated columns EE:EL and the other workbook sheets. The cached EE total is retained solely as provenance and is not treated as an independent measurement.
4. Preserve blanks as NULL with `missing` status. Explicit source zero would be `reported_zero`; a blank never becomes zero. The current source has no numeric zero ingredient cells.
5. Parse finite numerical values within 0–100 percentage points. The malformed value `0,002,` at BJ211 is retained as raw text, with a NULL numeric value, and its profile is held for review. No decimal-separator correction is guessed.
6. Verify the 18 ingredient formulas using a restricted decimal-literal addition parser. All match their cached results within 1e-9 percentage points. Both original formula and original cached value are retained. Cell references, functions, arbitrary expressions, and mismatching formula results would be held for review. No executable evaluation is used.
7. Calculate a diagnostic sum of the original source ingredient columns without changing values. Twenty profiles fall outside the configured 95–105% review range and are held for review. Incomplete reporting and overlapping labels may explain these totals. The threshold is an import policy, not a biological rule.
8. Detect identical name/location/evidence-type/raw-composition records as duplicate candidates. Retain and hold all members of such a group rather than selecting a sample arbitrarily. No candidates were found under this exact criterion; near duplicates and shared underlying studies have not been adjudicated.
9. Keep every ingredient label distinct. CTL and CLP (Snaclec), for example, are separate. Parent relationships are NULL until reviewed. No family totals or normalized proportions are created.

There are **24 blocking issue entries across 23 profiles**: 20 out-of-range totals, two unknown measurement types, one malformed number, and one empty composition. The empty composition overlaps an unknown-type profile. The broader review queue also includes 25 informational entries (seven label corrections and 18 verified formulas) and 117 dictionary review items.

## Reading the database

Use `ready_profiles` and `ready_components` for the structurally eligible subset. Use `profiles` and `components` to inspect everything, including held records.

```sql
-- Measured venom profiles, kept separate from gene-expression profiles.
SELECT profile_id, species_name, location
FROM ready_proteomic_profiles;

-- Original ingredient categories for one profile.
SELECT d.original_label, c.abundance_pct, c.value_status, c.source_cell
FROM ready_components AS c
JOIN toxin_dictionary AS d USING (toxin_id)
WHERE c.profile_id = ?;

-- Gene-expression evidence has a separate view.
SELECT * FROM ready_transcriptomic_profiles;
```

`named_components` contains only the 13 explicitly named labels from eligible profiles. It is NOT a full composition: summing it would omit unreviewed categories. Use the full distinct-label record when retaining a source profile, and do not automatically sum or merge biological categories.

Percentages are stored in percentage points: `25.3` means 25.3%, not the fraction 0.253. Across studies the abundance denominator and methods may differ. Transcriptomic percentages describe expression, not measured venom protein abundance.

## Review once, then rerun

Run from the project folder:

```sh
python3 scripts/clean_venom_data.py
python3 -m unittest discover -s tests -v
```

Reusable label mappings live in `config/cleaning_rules.json`. Adding a verified toxin label supplies its `canonical_id` and `name`; distinct source labels are still not merged. Keep mappings supported by the source literature.

For a supported measurement-type or species-label correction, put the full profile ID in `profile_overrides`, along with an evidence-based `reason`. Accepted override fields are `measurement_type`, `species_name`, and `reason`. No numeric, total, or duplicate-review override is currently implemented; these records intentionally remain held until a source-supported correction mechanism is added. Never fix a disputed number by editing the raw workbook.

Example structure, using an actual profile ID only after finding evidence:

```json
{
  "profile_overrides": {
    "PROFILE_ID_FROM_EXCEPTION_FILE": {
      "measurement_type": "proteomics",
      "reason": "Verified against the cited original study, table/page ..."
    }
  }
}
```

The database is rebuilt deterministically. Source content hashes are part of profile IDs, so replacing the source workbook with a different version cannot silently attach old overrides to new records. A new output may be written with `--output /absolute/path/to/disposable/folder`.

## Remaining limits

- Species names are formatted, not taxonomically reconciled.
- Profiles cite the dataset and exact workbook row. Primary-study citations are not invented where this sheet does not supply them.
- Review range acceptance does not establish completeness, analytical comparability, or a non-overlapping family hierarchy.
- The other downloaded sources are not yet combined with this workbook.
- No normalization, averaging, imputation, correlations, ML, or venom-effect inference was performed.

Validation includes unit tests for missing-versus-zero, malformed numbers, name preservation, evidence-type separation, formula verification, non-normalization, unknown labels, and duplicate retention. The full import checks database integrity, foreign keys, and the unchanged source checksum. An independent XML-to-database reconciliation and reproducibility check are recorded in `reports/cleaning_validation.json`.

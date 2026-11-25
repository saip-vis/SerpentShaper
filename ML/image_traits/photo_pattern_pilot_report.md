# Photo-observed marking pilot

This exploratory experiment asks whether venom categories linked by a source species label can predict whether prominent repeated markings are visible on the body section of an accepted photo. It does not predict an entire animal or establish that venom causes a pattern.

## Evidence

Fifty-three individually inspected photos from 53 observations and 53 source labels have visible-body annotations: 37 show prominent repeated markings, 16 do not. The initial eight-photo pilot was expanded by 45 photos after intermediate results were reviewed; four were specifically chosen to improve coverage of unpatterned examples. This is development data, **not an untouched test set**. See [labels and evidence](photo_pattern_pilot_labels.json) and [detailed results](photo_pattern_pilot_results.json).

The 45 additional source decisions are recorded as assistant reviews in their manifests. They use iNaturalist research-grade community identifications and visual checks, not independent expert verification. They describe visible areas only; concealed parts could not be assessed. Venom profiles and photographs are associated by species label, not a shared individual. Species labels and license records may still need verification for the intended use.

## Development comparison

A fixed logistic regression and a training-species prevalence baseline were compared using leave-one-genus-out folds. Imputation, missingness indicators, and scaling are fitted inside each training fold; training species receive equal total weight, and held-out venom profiles are averaged by species.

| Measure | Logistic regression | Prevalence baseline |
| --- | ---: | ---: |
| Brier score; lower is better | 0.355 | 0.231 |
| Balanced accuracy at 0.5 threshold | 0.441 | 0.500 |
| Recall on visibly unpatterned examples | 2/16 | 0/16 |
| Recall on visibly patterned examples | 28/37 | 37/37 |

The model underperformed this baseline on the development comparison. Fifty-three examples and one coarse pattern label do not establish a reliable result, so this model has **not** been connected to the main interface. These numbers describe a narrow photo-label task, not the accuracy of generating an imagined snake.

## Reproduce

From the repository root, with Python, NumPy, scikit-learn, and the original local photos:

```sh
python3 scripts/evaluate_photo_pattern_pilot.py
python3 -m unittest tests.test_photo_pattern_experiment
```

The evaluator enforces the source-image gate, rejects reserved observations and duplicate species or observation IDs, checks hashes, and fits preprocessing inside each training fold. Additional traceably reviewed examples, fuller phenotype labels, and a separate held-out evaluation are needed before this experiment can inform renderer controls.

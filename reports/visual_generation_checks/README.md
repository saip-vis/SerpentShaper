# Venom-to-illustration checks

These checks assess an experimental illustration system, not the true appearance of a snake inferred from venom. The eight source profiles below were used in training, and the comparison artwork is authored project work rather than verified anatomical ground truth. Hypothetical intermediate venoms have no known correct image for comparison.

## Changes and visual comparisons

[comparison.png](comparison.png) shows the current output beside eight authored references; [before_fix_comparison.png](before_fix_comparison.png) records the earlier output. In addition to smoothing the model's handling of values near zero, the renderer can now draw a smoothly flattened tail and pale accents along bands. Both new controls are trained on categories in the authored designs, not measured animal anatomy. In the coral-snake training example the new pale accents are visible, although the band sequence and colors are approximate. The sea-snake example gains a flattened tail, but does not match the reference's dark/yellow coloring. The monocled cobra also receives some false tail flattening. The cobra pose and monocle and the diamondback's markings and rattle remain imperfect.

The image model still uses just nine body-color patches from eight species. It does **not** train the anatomy from photographs. Its small photo-color evaluation had a mean channel error of 35.3/255 compared with 33.2/255 for its simple baseline. The output is not a validated biological prediction.

## Slider checks

[transition.png](transition.png) shows 100 increments from one recorded western diamondback profile to one monocled cobra profile. Missing source values are treated as zero for this engineering exercise, not asserted to be absent from those samples. Before the changes the largest step in the original 12 design controls was **0.495** on a 0–1 scale. Afterward, the largest step across all 14 current controls was **0.140**. The largest change in a corresponding body point or radius fell from approximately **29.18** to **10.35 SVG units**. These are changes per one-hundredth of the entire profile blend, not one percentage point of a single toxin, and do not guarantee smoothness along all paths. Colors and scale sampling also have discrete rendering steps.

Four additional 100-step paths were exercised. For the original 12 controls, the pre-change maximum changes were 0.195, 0.094, 0.164 and 0.225. The corresponding current maxima, including the two additional controls, were 0.089, 0.091, 0.069 and 0.102. Details and the current inputs are in [results.json](results.json). The older full results are preserved in [before_fix_results.json](before_fix_results.json).

All 12 toxin categories were individually changed from zero to 10% and then restored to zero in a fixed input. Controls, colors and body geometry returned to their original state in all 12 cases. The illustration model uses a two-percentage-point near-zero ramp and a reduced missingness weight; the separate photo-color model retains its one-point ramp. These are numerical conventions, not biological claims.

## Generalization remains limited

The existing shape development evaluation holds out complete genera, but those folds were examined during model selection and are not an untouched final test. For example, its held-out *Crotalus atrox* diamond control is approximately 0.03 despite a visible diamond pattern in the reserved reference photo. Its held-out *Naja kaouthia* hood control is about 0.20 against an authored target of 1.0, and its held-out *Micrurus alleni* band control is about 0.30 against a target of 1.0. These are normalized illustration controls, not probabilities or measured animal features. The reserved photo-pattern check contains only three partial or single views and cannot establish overall accuracy.

[smoothing_candidates.json](smoothing_candidates.json) records candidate shape preprocessing comparisons, including their effects on development folds. The chosen 2-point ramp and 0.25 missingness scale trades some individual reference fidelity for smoother behavior on tested paths. It does not fix the underlying shortage of paired, measured morphology and venom data. [before_fix_smoothing_candidates.json](before_fix_smoothing_candidates.json) preserves the previous experiment, in which photo preprocessing was also varied; its numbers should not be compared directly with the current shape-only experiment.

## Reproduce

From the repository root, with Node, Python with NumPy and scikit-learn, Pillow, and `rsvg-convert`:

```sh
python3 scripts/train_connected_prototype.py
node scripts/evaluate_visual_generation.cjs
python3 scripts/evaluate_smoothing_candidates.py
python3 scripts/render_visual_checks.py
```

Training and the candidate experiment require the original reviewed local photo files. The candidate experiment does not overwrite the product model. The visual check creates temporary SVGs in the ignored `.work/` directory, and the render step creates the current PNGs. No downloaded source photos are copied into this report.

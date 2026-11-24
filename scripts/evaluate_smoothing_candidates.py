"""Compare exploratory preprocessing settings without modifying product models.

This uses the same development folds as the current model, not a final test.
Run with NumPy, scikit-learn and the existing local reviewed photo files.
"""
import hashlib
import json
import statistics
from pathlib import Path

import train_connected_prototype as connected

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/visual_generation_checks/smoothing_candidates.json'
CASES = ['Crotalus atrox', 'Naja kaouthia', 'Dendroaspis polylepis', 'Micrurus alleni', 'Bungarus multicinctus']


def main():
    controls, profiles = connected.load_profiles()
    feature_ids = [c['id'] for c in controls]
    left = profiles['Crotalus atrox'][0]['features']
    right = profiles['Naja kaouthia'][0]['features']
    original_settings = (connected.SHAPE_ACTIVATION_WIDTH, connected.SHAPE_MISSINGNESS_SCALE)
    results = []
    try:
        for width, scale in [(1.0, 1.0), (2.0, .1), (2.0, .25), (3.0, .25), (5.0, 1.0)]:
            connected.SHAPE_ACTIVATION_WIDTH = width
            connected.SHAPE_MISSINGNESS_SCALE = scale
            model, report = connected.train()
            previous = None
            largest = {'difference': 0.0, 'trait': None, 'from_fraction': None, 'to_fraction': None}
            for i in range(101):
                fraction = i / 100
                values = [(a or 0) * (1-fraction) + (b or 0) * fraction for a, b in zip(left, right)]
                prediction = connected.predict([{'features': values}], model)[0]
                if previous is not None:
                    for j, trait in enumerate(connected.TRAITS):
                        difference = abs(float(prediction[j] - previous[j]))
                        if difference > largest['difference']:
                            largest = {'difference': difference, 'trait': trait, 'from_fraction': (i-1)/100, 'to_fraction': fraction}
                previous = prediction
            case_results = {}
            for name in CASES:
                prediction = connected.predict([profiles[name][0]], model)[0]
                targets = dict(zip(connected.TARGETS, prediction.tolist()))
                case_results[name] = {k: targets[k] for k in ('hood', 'diamond', 'rattle', 'bands', 'monocle')}
            evaluation = report['evaluation']
            results.append({'activation_width_percentage_points': width, 'missingness_indicator_scale': scale,
                            'largest_adjacent_shape_control_change': largest,
                            'mean_development_holdout_mae_across_design_controls': statistics.mean(evaluation['mae_by_target'][k] for k in connected.TRAITS),
                            'mean_baseline_mae_across_design_controls': statistics.mean(evaluation['baseline_mae_by_target'][k] for k in connected.TRAITS),
                            'photo_color_mae_8bit': report['photo_evaluation']['model_mae_8bit'], 'training_example_controls': case_results})
    finally:
        connected.SHAPE_ACTIVATION_WIDTH, connected.SHAPE_MISSINGNESS_SCALE = original_settings
    source = ROOT / 'MainInterface/connected-model.js'
    result = {'status': 'experimental_candidates_not_installed',
              'purpose': 'Assess shape preprocessing tradeoffs without changing the product bundle. Photo preprocessing stays unchanged.',
              'limitations': ['The same development holdout folds informed previous model selection and are reused here; they are not an independent final test.',
                              'A 100-step synthetic interpolation is only one path and does not prove biological plausibility.',
                              'Missing inputs are treated as zero only for this exercise, not claimed to be absent in a venom sample.',
                              'Control outputs describe authored designs and are not biological probabilities.'],
              'current_bundle_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'feature_ids': feature_ids, 'results': results}
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    for entry in results:
        print('width', entry['activation_width_percentage_points'], 'indicator scale', entry['missingness_indicator_scale'],
              'max change', round(entry['largest_adjacent_shape_control_change']['difference'], 3),
              'design MAE', round(entry['mean_development_holdout_mae_across_design_controls'], 3),
              'photo MAE', round(entry['photo_color_mae_8bit'], 1))


if __name__ == '__main__':
    main()

"""Train an explicitly provisional direct venom-to-illustration prototype.

Anatomy is supervised by existing authored SVG designs; it is not measured
from animals. A separate photo-patch model adds a limited color cue only.
The two datasets are linked to venom by source label, not individual snake.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
from sklearn.kernel_ridge import KernelRidge
from sklearn.model_selection import LeaveOneGroupOut

from build_learned_training_data import ROOT, DB, SPEC, FLAGS, load_profiles, sha
from train_learned_morphology import ACTIVATION_WIDTH, medians_for, transform
from train_photo_color_pilot import run as train_photo_colors

PRESETS = ROOT / 'PhysicalRendererTest/presets/species-presets.json'
OUT = ROOT / 'MainInterface/connected-model.js'
REPORT = ROOT / 'ML/learned_morphology/connected_prototype.json'
TRAITS = ['headWidth', 'headLength', 'bodyWidth', 'hood', 'diamond', 'monocle',
          'rattle', 'tailTaper', 'bands', 'blotches', 'markSpacing', 'scaleDetail',
          'paddle', 'bandAccent']
COLORS = [f'{group}_{channel}' for group in ['skin', 'marking', 'belly'] for channel in 'rgb']
TARGETS = TRAITS + COLORS
GAMMA = 1.0
ALPHA = .05
SHAPE_ACTIVATION_WIDTH = 2.0
SHAPE_MISSINGNESS_SCALE = .25


def rgb(value):
    if not isinstance(value, str) or len(value) != 7 or value[0] != '#':
        raise ValueError('Expected a six-digit preset color')
    return [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]


def targets(preset):
    p = preset['artistic_parameters']
    plan, pattern = p['body_plan'], p['pattern']
    if plan == 'cobra':
        # Cobra and non-cobra designs use different projections. These are
        # explicitly authored transfer choices, not measured anatomy.
        head_width, head_length = .48, .58
        body_width = float(p['hood_profile'][0][1]) / 50
    else:
        h = p['head_geometry']
        vertical = [abs(seg[i]) for side in ('upper', 'lower') for seg in h[side] for i in (1, 3, 5, 7)]
        head_width, head_length = max(vertical) / 30, float(h['length']) / 100
        body_width = max(float(x[2]) for x in p['body_stations']) / 35
    tail = {'short': .75, 'long': .2, 'pointed': .4, 'rattle': .65, 'paddle': .35}.get(p['tail_type'], .5)
    bands = pattern in {'crossbands', 'band_sequence', 'rings', 'dotted_bands', 'coral_triads'}
    blotches = pattern in {'blotches', 'trapezoids', 'dorsal_zigzag', 'flank_triangles', 'hooks',
                           'mottled', 'ocelli', 'chevrons', 'speckled', 'gaboon', 'reticulated',
                           'hourglass', 'paired_ocelli', 'paired_spots'}
    vals = [head_width, head_length, body_width, float(plan == 'cobra'),
            float(pattern in {'diamonds', 'outlined_diamonds'}), float(pattern in {'monocle', 'spectacle'}),
            float(p['tail_type'] == 'rattle'), tail, float(bands), float(blotches),
            (float(p['mark_spacing']) - 20) / 100, (float(p['scale_pitch']) - 3) / 9,
            float(p['tail_type'] == 'paddle'), float(pattern in {'coral_triads', 'band_sequence'})]
    vals += rgb(p['skin_color']) + rgb(p['marking_color']) + rgb(p['belly_color'])
    return [float(np.clip(v, 0, 1)) for v in vals]


def matrix(rows, medians):
    return np.asarray([transform(r['features'], medians, SHAPE_ACTIVATION_WIDTH, SHAPE_MISSINGNESS_SCALE) for r in rows], dtype=float)


def fit(rows, n):
    medians = medians_for(rows, n)
    counts = Counter(r['species'] for r in rows)
    weights = np.asarray([1 / counts[r['species']] for r in rows])
    x = matrix(rows, medians)
    y = np.asarray([r['targets'] for r in rows])
    baseline = np.average(y, axis=0, weights=weights)
    model = KernelRidge(alpha=ALPHA, kernel='rbf', gamma=GAMMA).fit(x, y-baseline, sample_weight=weights)
    return {'median': medians, 'training_vectors': x.tolist(), 'dual_coefficients': model.dual_coef_.tolist(),
            'intercepts': baseline.tolist(), 'kernel_gamma': GAMMA}


def predict(rows, model):
    x = matrix(rows, model['median'])
    vectors = np.asarray(model['training_vectors'])
    distances = ((x[:, None, :] - vectors[None, :, :]) ** 2).sum(axis=2)
    return np.clip(np.exp(-model['kernel_gamma'] * distances) @ np.asarray(model['dual_coefficients']) + model['intercepts'], 0, 1)


def evaluate(rows, n):
    groups = np.asarray([r['species'].split()[0] for r in rows])
    records = []
    for train_idx, test_idx in LeaveOneGroupOut().split(np.zeros((len(rows), 1)), groups=groups):
        train = [rows[int(i)] for i in train_idx]
        test = [rows[int(i)] for i in test_idx]
        model = fit(train, n)
        pred = predict(test, model)
        train_by_species = {}
        for r in train:
            train_by_species.setdefault(r['species'], []).append(r['targets'])
        baseline = np.mean([np.mean(v, axis=0) for v in train_by_species.values()], axis=0)
        for species in sorted({r['species'] for r in test}):
            indices = [i for i, r in enumerate(test) if r['species'] == species]
            actual = np.mean([test[i]['targets'] for i in indices], axis=0)
            predicted = np.mean(pred[indices], axis=0)
            records.append({'species': species, 'actual': actual.tolist(), 'predicted': predicted.tolist(),
                            'baseline': baseline.tolist()})
    errors = np.asarray([np.abs(np.asarray(r['actual']) - r['predicted']) for r in records])
    base_errors = np.asarray([np.abs(np.asarray(r['actual']) - r['baseline']) for r in records])
    return {'method': 'leave-one-genus-out, averaged per held-out source label', 'held_out_species': len(records),
            'selection_note': 'Development results were inspected when choosing the kernel; these folds are not an untouched final test.',
            'mae_by_target': dict(zip(TARGETS, errors.mean(axis=0).tolist())),
            'baseline_mae_by_target': dict(zip(TARGETS, base_errors.mean(axis=0).tolist())), 'species_results': records}


def train():
    controls, profiles = load_profiles()
    preset_rows = json.loads(PRESETS.read_text())['presets']
    presets = {p['source_species_name']: p for p in preset_rows}
    rows = []
    for species, species_profiles in profiles.items():
        if species not in presets:
            continue
        y = targets(presets[species])
        for profile in species_profiles:
            rows.append({'species': species, 'common_name': presets[species].get('common_name'),
                         'profile_id': profile['profile_id'], 'features': profile['features'], 'targets': y})
    if len({r['species'] for r in rows}) < 4:
        raise ValueError('Not enough source species for grouped evaluation')
    photo = train_photo_colors()
    ids = [c['id'] for c in controls]
    if photo['feature_ids'] != ids:
        raise ValueError('Photo and anatomy venom controls do not match')
    params = fit(rows, len(ids))
    evaluation = evaluate(rows, len(ids))
    parity = predict([rows[0]], params)[0]
    for channel in 'rgb':
        p = photo['models']['patch_' + channel]
        px = transform(rows[0]['features'], p['median'])
        photo_value = float(np.clip(p['intercept'] + np.dot(p['coefficients'], px), 0, 1))
        idx = TARGETS.index('skin_' + channel)
        parity[idx] = .85 * parity[idx] + .15 * photo_value
    model = {'schema_version': 1, 'status': 'experimental_hybrid_not_biological_prediction',
             'model_id': 'connected-kernel-ridge-pilot-1', 'feature_ids': ids, 'targets': TARGETS,
             'activation_width_percentage_points': SHAPE_ACTIVATION_WIDTH,
             'shape_missingness_scale': SHAPE_MISSINGNESS_SCALE,
             'photo_activation_width_percentage_points': ACTIVATION_WIDTH, **params,
             'training_sources': [{'species': r['species'], 'common_name': r['common_name'],
                                   'profile_id': r['profile_id'], 'features': r['features']} for r in rows],
             'photo_sources': [{'species': r['species_label'], 'image_id': r['image_id'],
                                'photo_page': r['photo_page'], 'attribution': r['attribution'],
                                'license': r['photo_license']} for r in photo['image_records']],
             'photo_color_models': photo['models'], 'photo_color_strength': .15,
             'provenance': {'authored_preset_species': len({r['species'] for r in rows}),
                            'venom_profile_rows': len(rows), 'photo_count': photo['data']['photo_count'],
                            'photo_species': photo['data']['source_species_count'],
                            'link_scope': 'source label only; venom and photos are not matched individuals'}}
    report = {**model, 'status': 'experimental_hybrid_not_biological_prediction',
              'training_method': 'Species-equal multi-output RBF kernel ridge (gamma 1, alpha .05), two-point ramp and scaled missingness for direct venom features. Photo color retains a one-point ramp. No species identifier is an inference feature.',
              'evaluation': evaluation,
              'photo_evaluation': {'model_mae_8bit': photo['mean_channel_mae_8bit'],
                                   'baseline_mae_8bit': photo['baseline_mean_channel_mae_8bit']},
              'input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [DB, SPEC, FLAGS, PRESETS, Path(__file__).resolve(),
                               ROOT / 'scripts/train_learned_morphology.py', ROOT / 'scripts/build_learned_training_data.py']},
              'photo_inputs_sha256': photo['input_sha256'],
              'parity_example': {'features': rows[0]['features'], 'expected_outputs': dict(zip(TARGETS, parity.tolist()))},
              'versions': {'numpy': np.__version__, 'scikit_learn': sklearn.__version__},
              'limitations': ['Anatomy targets are translated from hand-authored illustrations, not measured image morphology.',
                              'The renderer approximates motif categories, not all natural patterns.',
                              'The image model predicts only a small patch color, not the color of a whole snake.',
                              'Venom and images are joined by species label, not verified individual specimens.',
                              'The output is an illustrative concept, not a species identification or calibrated prediction.']}
    return model, report


def main():
    model, report = train()
    OUT.write_text('// Generated by scripts/train_connected_prototype.py. Experimental; see report.\nwindow.SERPENT_CONNECTED_MODEL = ' + json.dumps(model, separators=(',', ':'), allow_nan=False) + ';\n')
    REPORT.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': model['status'], 'provenance': model['provenance'],
                      'held_out_species': report['evaluation']['held_out_species'],
                      'photo_mae_8bit': report['photo_evaluation']}, indent=2))


if __name__ == '__main__':
    main()

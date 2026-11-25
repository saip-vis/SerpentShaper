"""Reproduce the expanded photo-color development experiment.

The separate stages can run in different Python environments. This command
never overwrites the color model used by the main interface.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'ML/learned_morphology'
SAMPLES = DIRECTORY / 'mvp_body_patch_samples.json'
MEASUREMENTS = DIRECTORY / 'mvp_body_patch_measurements.json'
EXPERIMENT = DIRECTORY / 'mvp_body_patch_experiment.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('extract', 'train'))
    stage = parser.parse_args().stage
    if stage == 'extract':
        import extract_body_patch_pilot as extractor
        extractor.SAMPLES = SAMPLES
        result = extractor.extract()
        output = MEASUREMENTS
    else:
        import train_photo_color_pilot as trainer
        trainer.SAMPLES = SAMPLES
        trainer.MEASUREMENTS = MEASUREMENTS
        result = trainer.run()
        result['status'] = 'expanded_development_experiment_not_connected'
        result['limitations'][-1] = (
            'These coefficients were not connected to the main interface; '
            'the experiment is development data and not an untouched test.'
        )
        output = EXPERIMENT
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Wrote', output.relative_to(ROOT))


if __name__ == '__main__':
    main()

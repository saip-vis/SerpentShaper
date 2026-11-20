"""Export explicitly accepted, non-excluded rendering candidates; does not train a model."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def eligible(row):
    return (row.get('review_status') == 'accepted'
            and row.get('download_status') == 'downloaded'
            and not row.get('rendering_training_excluded', False)
            and not row.get('reference_only_exception', False)
            and not row.get('duplicate_of')
            and row.get('suitability_screening', {}).get('category') not in {'rejected', 'supplemental'})

def main():
    folder = ROOT / 'data/image_pilots'
    result = []
    for manifest in sorted(folder.glob('pilot_*/manifest.json')):
        for row in json.loads(manifest.read_text()):
            if eligible(row):
                path = (manifest.parent / row['local_path']).resolve()
                if not path.is_relative_to(manifest.parent.resolve()) or not path.is_file():
                    raise ValueError('Missing or unsafe image path: ' + row['image_id'])
                result.append(dict(row, batch=manifest.parent.name,
                                   local_path=str(path.relative_to(ROOT))))
    output = folder / 'rendering_manifest.json'
    output.write_text(json.dumps({'policy': 'config/image_review_policy.json',
        'note': 'Explicit review acceptance only; no model training performed.',
        'images': result}, indent=2)+'\n')
    print(f'{len(result)} eligible records written to {output}')

if __name__ == '__main__':
    main()

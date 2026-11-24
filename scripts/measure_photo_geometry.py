"""Measure manually marked, visible 2D features without inventing hidden anatomy.

The measurements are exploratory image projections, not renderer controls or
inferred physical characteristics. Run locally with Pillow and the source photos.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from build_learned_training_data import ROOT, build

ANNOTATIONS = ROOT / 'ML/learned_morphology/photo_geometry_annotations.json'
OUTPUT = ROOT / 'ML/learned_morphology/photo_geometry_measurements.json'


def pixel_point(point, width, height):
    if not isinstance(point, list) or len(point) != 2:
        raise ValueError('Each point must have two normalized coordinates')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in point):
        raise ValueError('Point coordinates must be finite and between 0 and 1')
    if width <= 0 or height <= 0:
        raise ValueError('Image dimensions must be positive')
    return (point[0] * width, point[1] * height)


def segment(a, b, width, height):
    pa, pb = pixel_point(a, width, height), pixel_point(b, width, height)
    distance = math.dist(pa, pb)
    if distance < 8:
        raise ValueError('Landmarks must be at least eight pixels apart')
    return distance


def measure(annotation, width, height):
    points = annotation.get('points', {})
    if not annotation.get('view') or not annotation.get('evidence'):
        raise ValueError('View and visible evidence are required')
    if annotation['measurement'] == 'apparent_head_height_to_length':
        length = segment(points['snout'], points['head_base'], width, height)
        apparent_height = segment(points['top'], points['bottom'], width, height)
        return {'head_length_pixels': length, 'head_height_pixels': apparent_height,
                'apparent_head_height_to_length': apparent_height / length}
    if annotation['measurement'] == 'apparent_marking_spacing_to_body_width':
        body_width = points['body_width']
        marks = points['mark_centers']
        if not isinstance(body_width, list) or len(body_width) != 2 or not isinstance(marks, list) or len(marks) < 3:
            raise ValueError('Pattern measurements need a width segment and at least three mark centers')
        width_px = segment(body_width[0], body_width[1], width, height)
        spacings = [segment(a, b, width, height) for a, b in zip(marks, marks[1:])]
        return {'body_width_pixels': width_px, 'adjacent_mark_spacing_pixels': spacings,
                'mean_apparent_marking_spacing_to_body_width': sum(spacings) / len(spacings) / width_px}
    raise ValueError('Unsupported geometry measurement')


def extract(overlay_dir=None):
    from PIL import Image, ImageDraw

    audit = build()
    candidates = {c['image_id']: c for c in audit['candidate_images']}
    annotations = json.loads(ANNOTATIONS.read_text())['annotations']
    records = []
    seen_observations = set()
    if overlay_dir is not None:
        overlay_dir.mkdir(parents=True, exist_ok=True)
    for ann in annotations:
        candidate = candidates.get(ann['image_id'])
        if not candidate or candidate['review_blocks']:
            raise ValueError('Source is not an accepted, unblocked candidate: ' + ann['image_id'])
        if candidate['observation_id'] in seen_observations:
            raise ValueError('Only one photo per observation is allowed in this pilot')
        seen_observations.add(candidate['observation_id'])
        manifest = ROOT / candidate['manifest']
        matches = [r for r in json.loads(manifest.read_text()) if r['image_id'] == ann['image_id']]
        if len(matches) != 1:
            raise ValueError('Ambiguous photo source')
        photo = matches[0]
        path = (manifest.parent / photo['local_path']).resolve()
        if not path.is_relative_to(manifest.parent.resolve()) or not path.is_file():
            raise ValueError('Missing or unsafe source image')
        if hashlib.sha256(path.read_bytes()).hexdigest() != candidate['sha256']:
            raise ValueError('Photo bytes do not match the review record')
        with Image.open(path) as original:
            width, height = original.size
            result = measure(ann, width, height)
            if overlay_dir is not None:
                display = original.convert('RGB')
                draw = ImageDraw.Draw(display)
                pts = ann['points']
                if ann['measurement'] == 'apparent_head_height_to_length':
                    lines = [([pts['snout'], pts['head_base']], 'cyan'), ([pts['top'], pts['bottom']], 'red')]
                else:
                    lines = [(pts['body_width'], 'cyan'), (pts['mark_centers'], 'red')]
                for points, color in lines:
                    xy = [pixel_point(p, width, height) for p in points]
                    draw.line(xy, fill=color, width=max(3, round(width / 400)))
                    radius = max(5, round(width / 250))
                    for x, y in xy:
                        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
                display.thumbnail((1400, 1400))
                display.save(overlay_dir / (ann['image_id'] + '.jpg'), quality=90)
        records.append({'image_id': ann['image_id'], 'source_species_label': candidate['species'],
                        'observation_id': candidate['observation_id'], 'manifest': candidate['manifest'],
                        'photo_sha256': candidate['sha256'], 'photo_page': photo.get('photo_page'),
                        'attribution': photo.get('attribution'), 'photo_license': photo.get('photo_license'),
                        'view': ann['view'], 'measurement': ann['measurement'], 'evidence': ann['evidence'],
                        'image_size': [width, height], 'points': ann['points'], 'result': result})
    return {'schema_version': 1, 'status': 'exploratory_photo_geometry_not_renderer_training_labels',
            'method': 'Euclidean distances in image pixel coordinates from manually placed landmarks.',
            'limitations': ['Perspective, posture, visibility and landmark choices change apparent geometry.',
                            'Head height in a side view is not dorsal head width.',
                            'Mark centers are points on the visible projection, not measured distances along a 3D snake.',
                            'These measurements do not approve phenotype labels or establish venom causation.'],
            'annotation_sha256': hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(), 'records': records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--overlay-dir', type=Path, help='Optional local-only directory for review overlays')
    args = parser.parse_args()
    output = extract(args.overlay_dir)
    OUTPUT.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print('Measured', len(output['records']), 'visible-image traits; no renderer training labels were approved.')


if __name__ == '__main__':
    main()

"""Validate source-linked illustrative presets and emit a file://-compatible browser bundle."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    catalog = json.loads((ROOT / 'data/processed/species_catalog/catalog.json').read_text())
    identities = {s['species_id']: s['source_species_name'] for s in catalog['species']}
    presets, inputs, unavailable_external = [], [], []
    for path in sorted((ROOT / 'config/species_presets').glob('*.json')):
        p = json.loads(path.read_text())
        if identities.get(p['species_id']) != p['source_species_name']:
            raise ValueError(f'Catalog identity mismatch: {path.name}')
        if p['preset_id'] != path.stem or p['venom_trait_mapping'] is not None or p['biological_measurements'] is not None:
            raise ValueError(f'Invalid identity or unsupported biological defaults: {path.name}')
        if not p['evidence']['sources'] or not p['policy']['numeric_values_are_artistic']:
            raise ValueError(f'Missing evidence/policy: {path.name}')
        art = p['artistic_parameters']
        enums = {'body_plan': {'cobra', 'terrestrial', 'viper', 'marine'},
                 'pattern': {'monocle', 'spectacle', 'plain', 'diamonds', 'outlined_diamonds', 'ocelli', 'paired_ocelli', 'lateral_bicolor', 'paired_spots', 'dorsal_zigzag', 'coral_triads', 'band_sequence', 'gaboon', 'edged_scales', 'mottled', 'hourglass', 'crossbands', 'dotted_bands', 'rings', 'chevrons', 'blotches', 'speckled', 'reticulated', 'flank_triangles', 'trapezoids', 'hooks'},
                 'scale_texture': {'smooth', 'keeled'},
                 'tail_type': {'pointed', 'long', 'short', 'rattle', 'paddle'},
                 'head_style': {'triangular', 'coffin', 'rectangular', 'rounded'},
                 'pupil': {'round', 'vertical', 'horizontal'}}
        for key, allowed in enums.items():
            if art.get(key) not in allowed:
                raise ValueError(f'Unsupported {key}: {path.name}')
        if art['pattern'] == 'band_sequence':
            bands = art.get('band_sequence')
            if (not isinstance(bands, list) or len(bands) < 2 or not isinstance(bands[0], dict) or bands[0].get('color') != 'skin'
                or any(not isinstance(b, dict) or b.get('color') not in {'skin', 'marking', 'belly'}
                       or not isinstance(b.get('fraction'), (int, float)) or not math.isfinite(b['fraction'])
                       or b['fraction'] <= 0 for b in bands)
                or not math.isclose(sum(b['fraction'] for b in bands), 1, abs_tol=1e-6)):
                raise ValueError(f'Invalid band sequence: {path.name}')
        for key in ['skin_color', 'marking_color', 'belly_color']:
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', art[key]):
                raise ValueError('Invalid preset palette')
        for key in ['tail_band_dark', 'tail_band_light', 'neck_stripe_color', 'ocelli_center_color', 'scale_tip_color', 'dorsal_midline_color', 'dorsal_interspot_color', 'ventral_tail_light', 'ventral_band_dark', 'pattern_border_color', 'diamond_center_color']:
            if key in art and not re.fullmatch(r'#[0-9a-fA-F]{6}', art[key]):
                raise ValueError('Invalid tail band color: ' + key)
        for key in ['tail_band_length', 'tail_band_spacing', 'neck_stripe_length', 'tail_pattern_length', 'ventral_band_spacing']:
            if key in art and (not isinstance(art[key], (int, float)) or not math.isfinite(art[key]) or art[key] <= 0):
                raise ValueError('Invalid tail band dimension: ' + key)
        for key in ['chevron_width', 'chevron_border', 'tail_band_dark_fraction', 'neck_stripe_offset', 'neck_stripe_width', 'zigzag_width', 'dorsal_midline_width', 'ventrolateral_stripe_start', 'longitudinal_stripe_width']:
            if key in art and (not isinstance(art[key], (int, float)) or not math.isfinite(art[key]) or not 0 < art[key] < 1):
                raise ValueError('Invalid pattern fraction: ' + key)
        if 'longitudinal_stripe_offsets' in art:
            offsets = art['longitudinal_stripe_offsets']
            if not isinstance(offsets, list) or not offsets or not all(isinstance(x, (int, float)) and math.isfinite(x) and -1 <= x <= 1 for x in offsets):
                raise ValueError('Invalid longitudinal stripe offsets')
        if 'rattle_size' in art and (not isinstance(art['rattle_size'], (int, float)) or not math.isfinite(art['rattle_size']) or not .4 <= art['rattle_size'] <= 2):
            raise ValueError('Invalid artistic rattle size')
        if 'lateral_boundary' in art and (not isinstance(art['lateral_boundary'], (int, float)) or not math.isfinite(art['lateral_boundary']) or not -1 < art['lateral_boundary'] < 1):
            raise ValueError('Invalid lateral boundary')
        if 'diamond_inner' in art and (not isinstance(art['diamond_inner'], (int, float)) or not math.isfinite(art['diamond_inner']) or not 0 < art['diamond_inner'] < .75):
            raise ValueError('Invalid diamond interior')
        if 'tail_pattern' in art and art['tail_pattern'] not in {'spots', 'alternating_bands'}:
            raise ValueError('Unsupported tail pattern')
        if art.get('tail_pattern') == 'alternating_bands' and not all(k in art for k in ('tail_band_light', 'tail_band_dark')):
            raise ValueError('Alternating tail bands need both colors')
        if 'ventral_pattern' in art and (art['ventral_pattern'] != 'bands' or 'ventral_band_dark' not in art):
            raise ValueError('Unsupported ventral pattern or missing band color')
        for key in ['body_build', 'scale_pitch', 'mark_spacing', 'mark_size']:
            if not isinstance(art[key], (int, float)) or not math.isfinite(art[key]) or art[key] <= 0:
                raise ValueError('Invalid artistic parameter: ' + key)
        def finite_sequence(values, length):
            return isinstance(values, list) and len(values) == length and all(
                isinstance(v, (int, float)) and math.isfinite(v) for v in values)
        if art['body_plan'] != 'cobra':
            head = art['head_geometry']
            if not finite_sequence(head['origin'], 2) or not finite_sequence(head['eye'], 4):
                raise ValueError('Invalid head landmarks')
            nostril = head.get('nostril')
            if not (finite_sequence(nostril, 2) or finite_sequence(nostril, 4)) or (len(nostril) == 4 and min(nostril[2:]) <= 0):
                raise ValueError('Invalid nostril landmark')
            for side, direction in [('upper', -1), ('lower', 1)]:
                segments = head[side]
                if not segments or not all(finite_sequence(seg, 8) for seg in segments):
                    raise ValueError('Invalid head outline segments')
                if segments[0][:2] != [0, 0] or segments[-1][-2:] != [head['length'], direction * head['neck']]:
                    raise ValueError('Head must join its explicit neck attachment')
                if any(a[-2:] != b[:2] for a, b in zip(segments, segments[1:])):
                    raise ValueError('Disconnected head outline')
            stations = art['body_stations']
            if len(stations) < 8 or not all(finite_sequence(v, 3) and v[2] >= 0 for v in stations) or stations[-1][2] != 0:
                raise ValueError('Invalid body stations or tail tip')
            if any(v[2] <= 0 for v in stations[:-1]):
                raise ValueError('Body width must remain positive before the tail tip')
        else:
            hood = art['hood_profile']
            if not all(finite_sequence(v, 2) and v[1] > 0 for v in hood) or any(a[0] >= b[0] for a, b in zip(hood, hood[1:])):
                raise ValueError('Invalid hood profile')
        if set(p['evidence']['reference_feature_map']) != {r['image_id'] for r in p['evidence']['photo_references']}:
            raise ValueError('Every reference needs a scoped feature note')
        for ref in p['evidence']['photo_references']:
            records = json.loads((ROOT / ref['manifest_path']).read_text())
            matches = [r for r in records if r.get('image_id') == ref['image_id']]
            if len(matches) != 1 or matches[0].get('sha256') != ref['sha256']:
                raise ValueError('Reference does not match photo manifest')
            if matches[0].get('review_status') in {'rejected', 'reference_only'} or matches[0].get('exclude_from_rendering'):
                raise ValueError('Excluded photo cannot be used as a healthy reference')
        for ref in p['evidence'].get('external_photo_references', []):
            source = (ROOT / ref['path']).resolve()
            cache = (ROOT / 'sources/image_research/modeling_reference_cache').resolve()
            if not source.is_relative_to(cache):
                raise ValueError('External reference cache/hash mismatch')
            if source.exists():
                if hashlib.sha256(source.read_bytes()).hexdigest() != ref['sha256']:
                    raise ValueError('External reference cache/hash mismatch')
            else:
                # Reference images are intentionally local-only; preserve their
                # provenance without pretending a missing file was verified.
                unavailable_external.append(ref['path'])
            if not ref.get('source_page') or not ref.get('scope') or not ref.get('attribution'):
                raise ValueError('External image needs provenance and use scope')
        presets.append(p)
        inputs.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if len({p['preset_id'] for p in presets}) != len(presets):
        raise ValueError('Duplicate preset ID')
    result = {'schema_version': 1, 'status': 'illustrative_presets_not_trained', 'inputs': inputs, 'presets': presets}
    target = ROOT / 'PhysicalRendererTest/presets'
    target.mkdir(exist_ok=True)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    (target / 'species-presets.json').write_text(text + '\n')
    (target / 'species-presets.js').write_text('// Generated by scripts/build_species_presets.py; edit config/species_presets instead.\nwindow.SERPENT_PRESETS = ' + text + ';\n')
    print(f'Validated and bundled {len(presets)} catalog-linked presets.')
    if unavailable_external:
        print(f'{len(unavailable_external)} local-only external reference image(s) were unavailable and could not be hash-checked.')

if __name__ == '__main__':
    main()

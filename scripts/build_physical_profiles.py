"""Export traceable physical reference profiles for every species-catalog label.

Uses the pinned ReptTraits workbook and curated descriptions. No inferred traits,
image annotations, training, or changes to venom and image source records.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = 'data/raw/repttraits/ReptTraits dataset v1-2.xlsx'
EXTRACT = 'sources/morphology/repttraits_catalog_extract.json'
PUBLICATION = 'https://doi.org/10.1038/s41597-024-03079-5'
DATASET = 'https://doi.org/10.6084/m9.figshare.24572683'
FIELDS = {
    'maximum_total_length_mm': 'Maximum total length ("TL", mm)',
    'maximum_svl_mm': 'Maximum length ("SVL", mm)/straight carapace length for turtles ("SCL", mm)',
    'maximum_female_svl_mm': 'Maximum female length ("SVL", mm)/straight carapace length for turtles ("SCL", mm)',
    'maximum_male_svl_mm': 'Maximum male length ("SVL", mm)/straight carapace length for turtles ("SCL", mm)',
    'juvenile_svl_mm_ambiguous_statistic': 'Maximum juvenile length ("SVL", mm)/straight carapace length for turtles ("SCL", mm)',
    'dorsal_colour': 'Dorsal colour', 'dorsal_pattern': 'Dorsal pattern',
    'pupil_shape': 'Pupil Shape', 'fang_position': 'Fangs',
}
DESCRIPTIVE_FIELDS = ['body', 'head', 'tail', 'scales', 'pattern', 'ventral', 'eyes', 'special', 'variation']
# These are design controls only, deliberately without biological default values.
CONTROLS = {
    'body': ['trunk_width', 'trunk_taper'], 'head': ['head_outline', 'head_neck_transition'],
    'tail': ['tail_outline', 'tail_pattern'], 'scales': ['surface_texture'],
    'pattern': ['dorsal_palette', 'pattern_geometry', 'pattern_contrast'],
    'ventral': ['ventral_palette', 'ventral_pattern'], 'eyes': ['pupil_shape', 'iris_palette'],
    'special': ['special_feature_geometry', 'display_state'],
    'variation': ['life_stage_variant', 'sex_variant', 'locality_variant'],
}


def missing(value):
    return value is None or str(value).strip().casefold() in {'', 'na', 'n/a', 'none'}


def col_letter(number):
    result = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_workbook(root, catalog):
    import openpyxl  # Only extraction needs the bundled Python's optional dependency.
    names = {s['source_species_name'] for s in catalog['species']} | {s['lookup_name'] for s in catalog['species']}
    result = {'workbook': WORKBOOK, 'workbook_sha256': sha(root / WORKBOOK)}
    workbook = openpyxl.load_workbook(root / WORKBOOK, read_only=True, data_only=True)
    try:
        for title in ['Data', 'Sources of individual trait val']:
            rows = workbook[title].iter_rows(values_only=True)
            headers = next(rows)
            result[title] = [{'row': number, 'values': {h: v for h, v in zip(headers, row) if h}}
                             for number, row in enumerate(rows, 2) if row[0] in names]
        result['references'] = [{'row': n, 'text': r[0]} for n, r in enumerate(workbook['References'].iter_rows(values_only=True), 1) if r[0]]
        result['definitions'] = [list(row[:3]) for row in workbook['Trait definitions'].iter_rows(values_only=True)]
    finally:
        workbook.close()
    write_json(root / EXTRACT, result)
    return result


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def build(root, catalog, extracted, notes):
    data = {r['values']['Species']: r for r in extracted['Data']}
    citations = {r['values']['Species']: r for r in extracted['Sources of individual trait val']}
    if len(data) != len(extracted['Data']) or len(citations) != len(extracted['Sources of individual trait val']):
        raise ValueError('Duplicate species key in workbook extraction')
    headers = list(next(iter(data.values()))['values'])
    columns = {field: col_letter(i) for i, field in enumerate(headers, 1)}
    output = []
    starter = json.loads((root / 'evidence/starter_species_physical_profiles.json').read_text())
    starters = {s['species_id'] for s in starter['species']}
    for species in catalog['species']:
        name = species['source_species_name']
        # Exact-name matching first. Only the existing referenced image alias may be tried next.
        candidates = [name]
        if species.get('alias_reference'):
            candidates.append(species['lookup_name'])
        matches = [n for n in dict.fromkeys(candidates) if n in data]
        match = matches[0] if matches else None
        record = data.get(match)
        source = citations.get(match)
        traits = {}
        issues = []
        for key, header in FIELDS.items():
            raw = record['values'].get(header) if record else None
            value = None if missing(raw) else raw
            citation = source['values'].get(header) if source else None
            traits[key] = {'value': value, 'status': 'reported' if value is not None else 'not_reported',
                'raw_value': raw, 'source_column': header,
                'data_cell': f"Data!{columns[header]}{record['row']}" if record else None,
                'citation_cell': f"'Sources of individual trait val'!{columns[header]}{source['row']}" if source else None,
                'citation': None if missing(citation) else citation,
                'compilation_url': DATASET}
            if value is not None and key.endswith('_mm') and (not isinstance(value, (int, float)) or value <= 0):
                traits[key]['status'] = 'needs_review'
                issues.append('Nonpositive or nonnumeric length: ' + key)
        if traits['juvenile_svl_mm_ambiguous_statistic']['value'] is not None:
            traits['juvenile_svl_mm_ambiguous_statistic']['status'] = 'needs_review'
            issues.append('Juvenile column header says maximum but definition says mean; statistic unresolved.')
        supplement = notes.get(name)
        descriptions = {key: None for key in DESCRIPTIVE_FIELDS}
        if supplement:
            for key in DESCRIPTIVE_FIELDS:
                if key in supplement['traits']:
                    reference = supplement.get('trait_references', {}).get(key, {})
                    descriptions[key] = {'text': supplement['traits'][key],
                        'source_url': reference.get('source_url', supplement['source_url']),
                        'scope': reference.get('scope', supplement.get('evidence_scope', 'species_description')),
                        'source_locator': reference.get('locator')}
        starter_document = starter['profile_document'] if species['species_id'] in starters else None
        fields_missing = [key for key, value in descriptions.items() if value is None]
        controls = sorted({control for key, value in descriptions.items() if value for control in CONTROLS[key]})
        if any(traits[k]['value'] is not None for k in ('dorsal_colour', 'dorsal_pattern')):
            controls.extend(['dorsal_palette', 'pattern_contrast'])
        output.append({'species_id': species['species_id'], 'source_species_name': name,
            'pilot_folders': sorted({str(Path(i['manifest_path']).parent) for i in species['images']}),
            'venom_profile_ids': species['venom_profile_ids'],
            'compilation_match': {'status': 'exact_source_name' if match == name else 'existing_documented_alias' if match else 'unmatched',
                'workbook_species_name': match, 'alias_reference': species.get('alias_reference') if match and match != name else None,
                'family': record['values']['Family'] if record else None,
                'row': record['row'] if record else None},
            'compilation_traits': traits, 'descriptions': descriptions,
            'starter_profile_document': starter_document,
            'taxonomy_note': supplement['traits'].get('taxonomy') if supplement else None,
            'source_caveat': supplement['traits'].get('caveat') if supplement else None,
            'supplemental_reference': supplement['source_url'] if supplement else None,
            'coverage': {'status': 'starter_reference' if starter_document else 'descriptive_reference' if any(descriptions.values()) else 'compilation_only' if any(t['value'] is not None for t in traits.values()) else 'unresolved_reference',
                         'descriptive_fields_not_extracted': fields_missing},
            'rendering_proposals': {'status': 'design_controls_only_no_defaults', 'controls': sorted(set(controls)),
                'numerical_shape_ratios': None, 'absolute_color_values': None, 'venom_trait_mapping': None},
            'issues': issues})
    return output


def render_markdown(profiles, summary):
    lines = ['# Physical reference profiles: complete catalog', '',
        'Generated from ReptTraits v1-2 and curated species descriptions. Every catalog source label has an entry. Coverage differs by species; unknowns are explicit. The four detailed starter profiles remain authoritative companion documents.', '',
        '**Interpretation:** Workbook lengths are reported maxima, never typical adult sizes. SVL excludes the tail. Juvenile values have a header/definition conflict and require review. Color categories are coarse compilation labels, not an exhaustive palette or a rendering preset. A missing pattern is not evidence of a patternless snake. Dataset values can differ from field accounts, including the starter profiles; neither is silently overwritten.', '',
        '**Scope:** These are species references, not measurements or annotations of the pilot photographs. Descriptions and image review are independent. No phenotype is inferred from venom. Body/head ratios and absolute colors remain unset. Some references describe regional populations or historical species complexes. The original venom taxonomy is preserved.', '',
        f"Entries: {summary['catalog_labels']}; workbook matches: {summary['workbook_matches']}; with newly extracted descriptive traits: {summary['with_descriptive_traits']}; starter references: {summary['starter_references']}.", '',
        '[Data publication](https://doi.org/10.1038/s41597-024-03079-5) · [Dataset](https://doi.org/10.6084/m9.figshare.24572683) · [Starter profiles](../StarterSpeciesPhysicalProfiles.md)', '',
        'For the engine, join `data/processed/morphology/physical_profiles.json` to the species catalog on `species_id`. Citations and workbook cell addresses are preserved per trait. The workbook bibliography is retained in the extraction snapshot. Compilation facts, supplementary descriptions and proposed rendering controls remain separate.', '',
        '## Species index', '']
    for p in profiles:
        anchor = p['source_species_name'].lower().replace(' ', '-')
        lines.append(f"- [{p['source_species_name']}](#{anchor}) — {p['coverage']['status'].replace('_', ' ')}")
    for p in profiles:
        lines += ['', '## ' + p['source_species_name'], '',
            f"Catalog ID: `{p['species_id']}`. Family in workbook: {p['compilation_match']['family'] or 'unmatched'}. Profile coverage: {p['coverage']['status'].replace('_', ' ')}.", '',
            'Pilot folders: ' + (', '.join('`' + x + '`' for x in p['pilot_folders']) or 'No downloaded photos in the catalog.') + '', '',
            '### Size and compiled traits', '']
        for key, trait in p['compilation_traits'].items():
            label = key.replace('_', ' ')
            value = trait['value']
            if value is None:
                lines.append(f'- **{label}:** Not reported in the matched compilation record.' if p['compilation_match']['row'] else f'- **{label}:** No matched compilation record.')
            else:
                citation = trait['citation'] or 'Citation not populated'
                cell = trait['data_cell']
                lines.append(f'- **{label}:** {value}. Source: ReptTraits `{cell}`; {citation}.' + (' **Requires review.**' if trait['status'] == 'needs_review' else ''))
        lines += ['', '### Shape, surface and appearance', '']
        if p['starter_profile_document']:
            lines += ['See the existing [detailed starter description](../StarterSpeciesPhysicalProfiles.md) for this species. The compilation below/above is an additional source, not a replacement.', '']
        for key, description in p['descriptions'].items():
            text = description['text'] + f" [Source]({description['source_url']})" if description else 'No species-specific description extracted for this field; leave unknown.'
            lines.append(f'- **{key.capitalize()}:** {text}')
        lines += ['', '### Variation, limits and proposed rendering controls', '']
        if p.get('illustration_specification'):
            spec = p['illustration_specification']
            lines.append('- **Illustration readiness:** ' + spec['status'].replace('_', ' ') +
                         '. Not scientifically approved. See `config/illustration_specifications.json` and `reports/illustration_readiness.json`.')
        if p['taxonomy_note']:
            lines.append(f"- **Taxonomy:** {p['taxonomy_note']} [Reference]({p['supplemental_reference']})")
        if p['source_caveat']:
            lines.append('- **Source scope:** ' + p['source_caveat'])
        lines.extend('- **Data issue:** ' + issue for issue in p['issues'])
        lines += ['- **Unmeasured:** head/body width ratios, tail/body length ratios, calibrated colors and population distributions.',
            '- **Proposed controls:** ' + (', '.join('`' + c + '`' for c in p['rendering_proposals']['controls']) or 'Choose controls after obtaining a descriptive source or consulting the starter profile.') + '. These are interface/design suggestions, not biological measurements.',
            '- **Reference views:** full-body dorsal/lateral, head detail, and ventral detail only when relevant. No image review is required to read this profile.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-extract', action='store_true', help='Read the original XLSX using openpyxl; otherwise use its fingerprinted snapshot.')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'data/processed/species_catalog/catalog.json').read_text())
    extracted = extract_workbook(ROOT, catalog) if args.refresh_extract else json.loads((ROOT / EXTRACT).read_text())
    if extracted.get('workbook_sha256') != sha(ROOT / WORKBOOK):
        raise ValueError('Extraction does not match workbook. Rebuild with --refresh-extract using bundled Python.')
    notes = json.loads((ROOT / 'config/morphology_notes.json').read_text())['species']
    names = {s['source_species_name'] for s in catalog['species']}
    if set(notes) - names:
        raise ValueError('Supplement contains names outside the catalog')
    profiles = build(ROOT, catalog, extracted, notes)
    illustration = json.loads((ROOT / 'config/illustration_specifications.json').read_text())
    by_id = {p['species_id']: p for p in profiles}
    for species_id, brief in illustration['species'].items():
        if species_id not in by_id or brief['source_species_name'] != by_id[species_id]['source_species_name']:
            raise ValueError('Illustration brief does not match catalog identity: ' + species_id)
    audit = []
    for p in profiles:
        brief = illustration['species'].get(p['species_id'])
        gaps = [key for key in DESCRIPTIVE_FIELDS if p['descriptions'][key] is None]
        p['illustration_specification'] = {
            'path': 'config/illustration_specifications.json',
            'species_key': p['species_id'] if brief else None,
            'status': brief['status'] if brief else 'illustration_brief_not_written',
            'scientific_reference_approved': False,
            'unextracted_description_fields': gaps,
            'starter_companion_requires_manual_consultation': p['starter_profile_document'] is not None}
        audit.append({'species_id': p['species_id'], 'source_species_name': p['source_species_name'],
                      **p['illustration_specification']})
    summary = {'catalog_labels': len(profiles),
        'workbook_matches': sum(p['compilation_match']['row'] is not None for p in profiles),
        'with_descriptive_traits': sum(any(p['descriptions'].values()) for p in profiles),
        'starter_references': sum(p['starter_profile_document'] is not None for p in profiles),
        'coverage_statuses': dict(Counter(p['coverage']['status'] for p in profiles)),
        'unmatched_workbook_labels': [p['source_species_name'] for p in profiles if p['compilation_match']['row'] is None],
        'with_juvenile_statistic_conflict': sum(bool(p['issues']) for p in profiles),
        'compilation_only_labels': [p['source_species_name'] for p in profiles if p['coverage']['status'] == 'compilation_only'],
        'unresolved_reference_labels': [p['source_species_name'] for p in profiles if p['coverage']['status'] == 'unresolved_reference']}
    inputs = [WORKBOOK, EXTRACT, 'config/morphology_notes.json', 'config/illustration_specifications.json', 'evidence/starter_species_physical_profiles.json', 'docs/StarterSpeciesPhysicalProfiles.md', 'data/processed/species_catalog/catalog.json']
    result = {'schema_version': 1, 'status': 'reference_profiles_with_explicit_gaps',
        'sources': {'publication': PUBLICATION, 'dataset': DATASET, 'workbook': WORKBOOK},
        'inputs': [{'path': p, 'sha256': sha(ROOT / p)} for p in inputs],
        'policies': {'no_venom_trait_inference': True, 'no_image_reviews_changed': True,
                     'missing_is_not_absent': True, 'lengths_are_maxima_not_means': True},
        'summary': summary, 'profiles': profiles}
    write_json(ROOT / 'data/processed/morphology/physical_profiles.json', result)
    write_json(ROOT / 'reports/morphology_coverage.json', summary)
    write_json(ROOT / 'reports/illustration_readiness.json', {
        'scope': 'Specification audit, not an image review or anatomical validation.',
        'catalog_labels': len(profiles), 'briefs_written': len(illustration['species']),
        'scientific_reference_approved': 0, 'species': audit})
    docs = ROOT / 'docs/physical_profiles'
    docs.mkdir(parents=True, exist_ok=True)
    (docs / 'AllSpeciesPhysicalProfiles.md').write_text(render_markdown(profiles, summary))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

"""Deterministic ingestion of the 2023 raw venom sheet. No analytics or ML.

Writes a SQLite database plus flat CSV exports; never edits the source workbook.
Use --output for a disposable validation run. See reports/cleaning_report.md.
"""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sqlite3
import zipfile
import xml.etree.ElementTree as ET

from audit_sources import xlsx_sheets, NS, REL

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/raw/venom_diet_2023/Supp. Mat. 1.xlsx'
SHEET = 'RAW_DATABASE_VENOM'

def column_number(label):
    result = 0
    for c in label:
        result = result * 26 + ord(c) - 64
    return result

def normalize_species(value):
    return ' '.join((value or '').replace('_', ' ').split())

def parse_percentage(raw):
    if raw is None or not str(raw).strip():
        return None, 'missing'
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation:
        return None, 'invalid'
    if not value.is_finite() or not Decimal(0) <= value <= Decimal(100):
        return None, 'invalid'
    return value, 'reported_zero' if value == 0 else 'reported_positive'

def literal_sum(formula):
    """Only decimal literals joined by +. Never execute code or cell references."""
    if not re.fullmatch(r'\s*\d+(?:\.\d+)?(?:\s*\+\s*\d+(?:\.\d+)?)*\s*', formula or ''):
        return None
    return sum((Decimal(part.strip()) for part in formula.split('+')), Decimal(0))

def make_records(rows, rules, source_id, formulas=None):
    formulas = formulas or {}
    header = rows[0]['cells']
    # E:ED are source ingredient columns; EE:EL are derived calculations.
    cols = [c for c in header if 5 <= column_number(c) <= 134]
    if len(cols) != 130 or header.get('A') != 'Species' or header.get('EE') != 'total %':
        raise ValueError('Unexpected source layout: inspect workbook before importing.')
    labels = []
    for col in cols:
        original = header[col]
        known = rules['toxin_labels'].get(original)
        labels.append(dict(toxin_id=f'vd2023_{col}', source_column=col, original_label=original,
            canonical_id=known['canonical_id'] if known else None,
            display_name=known['name'] if known else original,
            mapping_status='named' if known else 'unreviewed',
            parent_toxin_id=None))
    profiles, components, issues = [], [], []
    def flag(profile_id, field, code, severity, original, detail):
        issues.append(dict(profile_id=profile_id, field=field, code=code,
                           severity=severity, original_value=original, detail=detail))
    for row in rows[1:]:
        cells, row_no = row['cells'], row['row']
        if not any(str(v).strip() for v in cells.values()):
            continue
        pid = f'{source_id}_r{row_no}'
        raw_type = cells.get('C', '')
        override = rules.get('profile_overrides', {}).get(pid, {})
        if set(override) - {'measurement_type', 'species_name', 'reason'}:
            raise ValueError(f'Unsupported override keys for {pid}')
        if override and not override.get('reason', '').strip():
            raise ValueError(f'Override requires an evidence/reason note: {pid}')
        kind = override.get('measurement_type', rules['measurement_aliases'].get(raw_type.strip().lower(), 'unknown'))
        if kind not in {'proteomics', 'transcriptomics', 'unknown'}:
            raise ValueError(f'Invalid measurement override for {pid}')
        species = override.get('species_name', normalize_species(cells.get('A')))
        if not species:
            flag(pid, 'species_name', 'missing_species', 'blocking', cells.get('A'), 'Species label is required.')
        if kind == 'unknown':
            flag(pid, 'measurement_type', 'unknown_measurement_type', 'blocking', raw_type,
                 'Resolve using the underlying source; do not infer from spelling similarity.')
        elif raw_type.strip().lower() == 'trancriptome':
            flag(pid, 'measurement_type', 'measurement_typo_corrected', 'info', raw_type,
                 'Applied explicit alias trancriptome -> transcriptomics.')
        if override:
            flag(pid, 'profile', 'documented_override', 'info', json.dumps(override), override['reason'])
        valid_sum = Decimal(0)
        valid_count = 0
        for col in cols:
            raw = cells.get(col)
            value, status = parse_percentage(raw)
            address = f'{col}{row_no}'
            formula = formulas.get(address)
            if value is not None:
                valid_sum += value
                valid_count += 1
            if status == 'invalid':
                flag(pid, address, 'invalid_percentage', 'blocking', raw,
                     'Expected a finite number from 0 to 100; original retained, numeric value NULL.')
            if formula:
                recomputed = literal_sum(formula)
                if recomputed is not None and value is not None and abs(recomputed-value) <= Decimal('0.000000001'):
                    flag(pid, address, 'literal_formula_verified', 'info', raw,
                         'Literal addition independently recomputed and matched cached value within 1e-9 percentage points. Original formula and cached value retained.')
                else:
                    flag(pid, address, 'formula_component', 'blocking', raw,
                         'Formula cannot be verified as a matching literal sum; cached value retained for review.')
            components.append(dict(profile_id=pid, toxin_id=f'vd2023_{col}',
                source_cell=address, raw_value=raw,
                abundance_pct=float(value) if value is not None else None,
                value_status=status, source_formula=formula))
        if not valid_count:
            flag(pid, 'components', 'no_numeric_composition', 'blocking', None, 'No valid numerical component values.')
        low, high = rules['total_review_range_pct']
        if valid_count and not Decimal(str(low)) <= valid_sum <= Decimal(str(high)):
            flag(pid, 'component_sum_pct', 'total_outside_review_range', 'blocking', str(valid_sum),
                 'Outside configured 95–105% review range; source values preserved without normalization. Incomplete reporting or overlapping labels require review.')
        profiles.append(dict(profile_id=pid, source_id=source_id, source_sheet=SHEET, source_row=row_no,
            species_original=cells.get('A'), species_name=species,
            taxonomy_status='unreconciled_source_label', location_original=cells.get('B'),
            location=' '.join((cells.get('B') or '').split()) or None,
            measurement_original=raw_type, measurement_type=kind,
            source_cached_total_raw=cells.get('EE'),
            component_sum_pct=float(valid_sum), numeric_component_count=valid_count,
            component_sum_note='Sum of source columns E:ED; not normalized or guaranteed non-overlapping.',
            duplicate_group=None, ingestion_status='pending',
            citation_status='dataset_level_only', raw_source_row_json=json.dumps(cells, ensure_ascii=False, sort_keys=True)))
    # Identical source records are candidates, not proof of duplicate biological samples.
    by_profile = defaultdict(list)
    for c in components:
        by_profile[c['profile_id']].append((c['toxin_id'], c['raw_value']))
    groups = defaultdict(list)
    for p in profiles:
        key = json.dumps([p['species_name'],p['location'],p['measurement_type'],by_profile[p['profile_id']]], sort_keys=True)
        groups[key].append(p)
    for key, group in groups.items():
        if len(group) > 1:
            gid = 'dup_' + hashlib.sha256(key.encode()).hexdigest()[:12]
            for p in group:
                p['duplicate_group'] = gid
                flag(p['profile_id'], 'profile', 'duplicate_candidate', 'blocking', gid,
                     'Same name, location, evidence type and raw ingredient values; retained for sample-identity review.')
    blocked = {i['profile_id'] for i in issues if i['severity'] == 'blocking'}
    for p in profiles:
        p['ingestion_status'] = 'needs_review' if p['profile_id'] in blocked else 'ready_with_caveats'
    positive = {c['toxin_id'] for c in components if c['value_status'] == 'reported_positive'}
    for label in labels:
        if label['mapping_status'] == 'unreviewed' and label['toxin_id'] in positive:
            flag(None, label['toxin_id'], 'unreviewed_toxin_label', 'dictionary_review', label['original_label'],
                 'Preserved as a distinct source category. No expansion, hierarchy or biological function inferred.')
    return profiles, components, labels, issues

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE sources(source_id TEXT PRIMARY KEY, path TEXT NOT NULL, sha256 TEXT NOT NULL, sheet TEXT NOT NULL, dataset_doi TEXT NOT NULL, unit_note TEXT NOT NULL);
CREATE TABLE profiles(profile_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id), source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL, species_original TEXT, species_name TEXT, taxonomy_status TEXT NOT NULL, location_original TEXT, location TEXT, measurement_original TEXT, measurement_type TEXT NOT NULL CHECK(measurement_type IN ('proteomics','transcriptomics','unknown')), source_cached_total_raw TEXT, component_sum_pct REAL, numeric_component_count INTEGER, component_sum_note TEXT, duplicate_group TEXT, ingestion_status TEXT NOT NULL CHECK(ingestion_status IN ('needs_review','ready_with_caveats')), citation_status TEXT, raw_source_row_json TEXT NOT NULL, UNIQUE(source_id,source_sheet,source_row));
CREATE TABLE toxin_dictionary(toxin_id TEXT PRIMARY KEY, source_column TEXT UNIQUE NOT NULL, original_label TEXT NOT NULL, canonical_id TEXT, display_name TEXT NOT NULL, mapping_status TEXT NOT NULL, parent_toxin_id TEXT REFERENCES toxin_dictionary(toxin_id));
CREATE TABLE components(profile_id TEXT NOT NULL REFERENCES profiles(profile_id), toxin_id TEXT NOT NULL REFERENCES toxin_dictionary(toxin_id), source_cell TEXT NOT NULL, raw_value TEXT, abundance_pct REAL CHECK(abundance_pct IS NULL OR abundance_pct BETWEEN 0 AND 100), value_status TEXT NOT NULL CHECK(value_status IN ('missing','invalid','reported_zero','reported_positive')), source_formula TEXT, PRIMARY KEY(profile_id,toxin_id), CHECK((value_status IN ('missing','invalid') AND abundance_pct IS NULL) OR (value_status='reported_zero' AND abundance_pct=0) OR (value_status='reported_positive' AND abundance_pct>0)));
CREATE TABLE review_queue(issue_id INTEGER PRIMARY KEY, profile_id TEXT REFERENCES profiles(profile_id), field TEXT NOT NULL, code TEXT NOT NULL, severity TEXT NOT NULL, original_value TEXT, detail TEXT NOT NULL);
CREATE INDEX component_toxin_idx ON components(toxin_id);
CREATE INDEX profile_species_idx ON profiles(species_name);
CREATE VIEW ready_profiles AS SELECT * FROM profiles WHERE ingestion_status='ready_with_caveats';
CREATE VIEW ready_proteomic_profiles AS SELECT * FROM ready_profiles WHERE measurement_type='proteomics';
CREATE VIEW ready_transcriptomic_profiles AS SELECT * FROM ready_profiles WHERE measurement_type='transcriptomics';
CREATE VIEW ready_components AS SELECT c.* FROM components c JOIN ready_profiles p USING(profile_id);
CREATE VIEW named_components AS SELECT c.*,d.canonical_id,d.display_name FROM ready_components c JOIN toxin_dictionary d USING(toxin_id) WHERE d.mapping_status='named';
'''

def write_csv(path, records):
    if not records:
        raise ValueError(f'Unexpected empty export: {path}')
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'data/processed/venom_diet_2023')
    args = parser.parse_args()
    output = args.output.resolve()
    if (ROOT/'data/raw').resolve() in [output,*output.parents]:
        raise ValueError('Output must not be inside data/raw.')
    rules_path = ROOT/'config/cleaning_rules.json'
    rules = json.loads(rules_path.read_text())
    original_bytes = SOURCE.read_bytes()
    digest = hashlib.sha256(original_bytes).hexdigest()
    source_id = 'vd2023_' + digest[:12]
    sheets = dict(xlsx_sheets(SOURCE))
    with zipfile.ZipFile(SOURCE) as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        sheet = next(s for s in workbook.findall('s:sheets/s:sheet',NS) if s.get('name') == SHEET)
        links = {x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        target = links[sheet.get(REL)]
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        root = ET.fromstring(z.read(target))
        formulas = {c.get('r'):c.find('s:f',NS).text for c in root.findall('.//s:c',NS) if c.find('s:f',NS) is not None}
    profiles, components, dictionary, issues = make_records(sheets[SHEET], rules, source_id, formulas)
    output.mkdir(parents=True, exist_ok=True)
    target = output/'serpentshaper.sqlite'
    tmp = output/'serpentshaper.sqlite.tmp'
    if tmp.exists():
        tmp.unlink()
    source = dict(source_id=source_id, path=str(SOURCE.relative_to(ROOT)), sha256=digest,
                  sheet=SHEET, dataset_doi='10.6084/m9.figshare.22179949.v1',
                  unit_note='Source relative abundances in percentage points; denominator and methods depend on original study. Transcript abundance is not venom protein abundance.')
    with sqlite3.connect(tmp) as conn:
        conn.executescript(SCHEMA)
        for table, records in [('sources',[source]),('profiles',profiles),('toxin_dictionary',dictionary),('components',components),('review_queue',issues)]:
            columns = list(records[0])
            conn.executemany(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
                             [[r[c] for c in columns] for r in records])
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        counts = {name:conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in
                  ['profiles','components','toxin_dictionary','review_queue','ready_profiles','ready_proteomic_profiles','ready_transcriptomic_profiles']}
    tmp.replace(target)
    for name, records in [('profiles',profiles),('components',components),('toxin_dictionary',dictionary),('review_queue',issues)]:
        write_csv(output/f'{name}.csv', records)
    profile_by_id = {p['profile_id']:p for p in profiles}
    exceptions = []
    for issue in issues:
        if issue['severity'] != 'blocking':
            continue
        p = profile_by_id[issue['profile_id']]
        exceptions.append(dict(profile_id=p['profile_id'], source_row=p['source_row'],
            species_name=p['species_name'], measurement_type=p['measurement_type'],
            field=issue['field'], issue=issue['code'], original_value=issue['original_value'], detail=issue['detail']))
    if exceptions:
        write_csv(output/'profile_exceptions.csv',exceptions)
    elif (output/'profile_exceptions.csv').exists():
        (output/'profile_exceptions.csv').unlink()
    (output/'cleaning_rules_snapshot.json').write_text(json.dumps(rules,indent=2)+'\n')
    summary = dict(source_sha256=digest, rules_sha256=hashlib.sha256(rules_path.read_bytes()).hexdigest(),
        schema_version=1, cleaner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_id=source_id, counts=counts,
        measurement_types=dict(Counter(p['measurement_type'] for p in profiles)),
        issues_by_code=dict(Counter(i['code'] for i in issues)),
        component_statuses=dict(Counter(c['value_status'] for c in components)),
        excluded_sheets=[name for name in sheets if name != SHEET],
        excluded_columns='D (empty unlabeled column); EE:EL (source-derived calculations, cached EE total retained only as provenance)',
        limitations=['Not a taxonomically reconciled dataset.', 'No per-profile primary citation assignment inferred.',
                     'Ready means structurally ingestible with caveats, not scientifically validated.',
                     'Unreviewed toxin labels remain distinct and are excluded from named_components.',
                     'Parent-child relationships are NULL until reviewed; no family aggregation performed.'])
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == digest
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()

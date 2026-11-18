"""Independently reconcile original XML cells with the ingestion outputs."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/processed/venom_diet_2023'
SOURCE = ROOT/'data/raw/venom_diet_2023/Supp. Mat. 1.xlsx'
N = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def run():
    with zipfile.ZipFile(SOURCE) as z:
        strings = [''.join(item.itertext()) for item in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        original = {}
        for cell in xml.iter(N+'c'):
            node = cell.find(N+'v')
            value = node.text if node is not None else ''
            if cell.get('t') == 's' and value:
                value = strings[int(value)]
            original[cell.get('r')] = value
    conn = sqlite3.connect(OUT/'serpentshaper.sqlite')
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    assert conn.execute("SELECT COUNT(*) FROM ready_profiles p JOIN review_queue q USING(profile_id) WHERE q.severity='blocking'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM ready_profiles WHERE measurement_type='unknown'").fetchone()[0] == 0
    checked = 0
    for address, raw, numeric, status in conn.execute('SELECT source_cell,raw_value,abundance_pct,value_status FROM components'):
        assert raw == original.get(address), (address,raw,original.get(address))
        if numeric is not None:
            assert math.isfinite(numeric) and 0<=numeric<=100
            assert math.isclose(numeric,float(raw),rel_tol=1e-14,abs_tol=1e-14)
        else:
            assert status in ('missing','invalid')
        checked += 1
    assert checked == 356*130
    for row_no, original_species, species, kind, raw_kind in conn.execute('SELECT source_row,species_original,species_name,measurement_type,measurement_original FROM profiles'):
        assert original_species == original.get(f'A{row_no}')
        assert raw_kind == original.get(f'C{row_no}')
        assert species == ' '.join(original_species.replace('_',' ').split())
    for table in ['profiles','components','toxin_dictionary','review_queue']:
        with (OUT/f'{table}.csv').open(newline='') as f:
            assert sum(1 for _ in csv.DictReader(f)) == conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    raw_verified = 0
    for item in json.loads((ROOT/'sources/download_manifest.json').read_text()):
        if item['status']=='downloaded' and item['path'].startswith('data/raw/'):
            assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']
            raw_verified += 1
    with tempfile.TemporaryDirectory(prefix='cleaning-validation-',dir=OUT.parent) as td:
        subprocess.run([sys.executable,str(ROOT/'scripts/clean_venom_data.py'),'--output',td],check=True,capture_output=True,text=True)
        for name in ['profiles.csv','components.csv','toxin_dictionary.csv','review_queue.csv','profile_exceptions.csv','summary.json','cleaning_rules_snapshot.json']:
            assert (OUT/name).read_bytes() == (Path(td)/name).read_bytes(), name
        # The schema has no clock-derived IDs or timestamps: identical input yields identical database bytes.
        assert (OUT/'serpentshaper.sqlite').read_bytes() == (Path(td)/'serpentshaper.sqlite').read_bytes()
    result = dict(status='passed', original_component_cells_reconciled=checked,
        profile_rows_reconciled=356, raw_download_hashes_verified=raw_verified,
        foreign_keys='passed', database_integrity='ok', csv_row_counts='matched_database',
        blocking_issues_excluded_from_ready_views=True,
        repeated_import='all_export_and_database_bytes_identical',
        scope='cleaning and ingestion validation only')
    (ROOT/'reports/cleaning_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    run()

"""Read-only audit of original CSV/XLSX sources, using Python standard library."""
from pathlib import Path
from collections import Counter
import csv
import io
import json
import posixpath
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

def xlsx_sheets(path_or_bytes):
    with zipfile.ZipFile(path_or_bytes) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in x.iter('{' + NS['s'] + '}t'))
                       for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rels = {x.get('Id'): x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = rels[sheet.get(REL)]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(z.read(target)).findall('s:sheetData/s:row', NS):
                values = {}
                for cell in row:
                    ref = cell.get('r', '')
                    value = cell.find('s:v', NS)
                    text = value.text if value is not None else ''
                    if cell.get('t') == 's' and text:
                        text = strings[int(text)]
                    elif cell.get('t') == 'inlineStr':
                        text = ''.join(x.text or '' for x in cell.findall('s:is/s:t', NS))
                    values[''.join(c for c in ref if c.isalpha())] = text
                rows.append({'row': int(row.get('r')), 'cells': values})
            yield sheet.get('name'), rows

def main():
    out = {}
    p = ROOT/'data/raw/museum_venomics/PublishedProteomes.csv'
    rows = list(csv.DictReader(p.open(encoding='utf-8-sig')))
    out['published_proteomes'] = {
        'profiles': len(rows), 'distinct_taxon_labels': len({r['Species2'] for r in rows}),
        'by_family': {f: {'profiles': sum(r['Family']==f for r in rows),
                          'taxon_labels': len({r['Species2'] for r in rows if r['Family']==f})}
                      for f in sorted({r['Family'] for r in rows})},
        'missing_doi_rows': sum(not r['DOI'].strip() for r in rows),
        'reported_total_outside_95_105': [{'csv_row': i+2, 'taxon': r['Species2'], 'reported_total': r['TOTAL']}
                                       for i,r in enumerate(rows) if not r['TOTAL'] or not 95<=float(r['TOTAL'])<=105],
        'columns': list(rows[0]),
        'warning': 'Distinct taxon labels are not reconciled accepted species; parent/subfamily toxin columns overlap.'}
    p = ROOT/'data/raw/museum_venomics/SummaryResults_ThisStudy.csv'
    if p.exists():
        records = list(csv.DictReader(p.open(encoding='utf-8-sig')))
        out['museum_experiment'] = {'rows': len(records), 'columns': list(records[0]),
            'sample_types': dict(Counter(r.get('Form_short', '') for r in records)),
            'taxon_labels': len({r.get('Species2') for r in records})}
    p = ROOT/'data/raw/venom_diet_2023/Supp. Mat. 1.xlsx'
    sheets = list(xlsx_sheets(p))
    raw = sheets[0][1]
    records = [r for r in raw[1:] if r['cells'].get('A')]
    out['venom_diet_2023'] = {'raw_records': len(records),
        'taxon_labels': len({r['cells']['A'] for r in records}),
        'analysis_types': dict(Counter(r['cells'].get('C', '') for r in records)),
        'header_cells': raw[0]['cells'],
        'non_elapid_viperid_candidate_taxa': sorted({r['cells']['A'] for r in records
              if r['cells']['A'].split('_')[0] in ['Atractaspis', 'Dispholidus', 'Thelotornis', 'Boiga',
                 'Oxybelis', 'Spilotes', 'Rhabdophis', 'Philodryas', 'Hypsiglena', 'Trimorphodon',
                 'Erythrolamprus', 'Oxyrhopus', 'Leioheterodon', 'Telescopus', 'Malpolon']}),
        'sheets': [{'name': name, 'nonempty_rows':len([r for r in rs if any(r['cells'].values())]),
                    'cached_error_cells':sum(v.startswith('#') for r in rs for v in r['cells'].values() if isinstance(v,str))}
                   for name,rs in sheets]}
    p = ROOT/'data/raw/squamatabase/diet.csv'
    if p.exists():
        records = list(csv.DictReader(p.open(encoding='utf-8-sig')))
        out['squamatabase'] = {'rows':len(records), 'columns':list(records[0]),
            'distinct_predator_labels':len({r['predator'] for r in records}),
            'published_proteome_exact_name_overlap':len({r['predator'] for r in records} & {r['Species2'] for r in rows})}
    p = ROOT/'data/raw/repttraits/ReptTraits dataset v1-2.xlsx'
    if p.exists():
        for name, rs in xlsx_sheets(p):
            if name != 'Data':
                continue
            records = [r['cells'] for r in rs[1:] if r['cells'].get('A')]
            snakes = [r for r in records if r.get('C') == 'Serpentes']
            out['repttraits'] = {'version':'v1-2','species_rows':len(records),
                'snake_rows':len(snakes), 'snake_family_counts':dict(Counter(r.get('D') for r in snakes)),
                'published_proteome_exact_name_overlap':len({r['A'] for r in snakes} & {r['Species2'] for r in rows}),
                'columns':rs[0]['cells']}
    out['archive_spreadsheets'] = []
    for p in (ROOT/'data/raw').rglob('*.zip'):
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                if name.endswith('.xlsx'):
                    stats = [{'name': n,'stored_rows': len(rs), 'first_rows':rs[:3]}
                             for n,rs in xlsx_sheets(io.BytesIO(z.read(name)))]
                    out['archive_spreadsheets'].append({'archive':str(p.relative_to(ROOT)), 'file':name,'sheets':stats})
                if name.endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(z.read(name))) as inner:
                        out.setdefault('nested_archives',[]).append({'archive':str(p.relative_to(ROOT)),
                            'inner':name,'files':inner.namelist()})
    (ROOT/'reports/data_audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['archive_spreadsheets']},indent=2,ensure_ascii=False))

if __name__ == '__main__':
    main()

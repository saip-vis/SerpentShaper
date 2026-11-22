"""Check input-catalog bindings and evidence traceability; no analytics or ML."""
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def validate_spec(spec, evidence, conn):
    errors=[]
    binding=spec['source_binding']
    actual=conn.execute('SELECT sha256,sheet,dataset_doi FROM sources WHERE source_id=?',(binding['source_id'],)).fetchone()
    if actual!=(binding['workbook_sha256'],binding['sheet'],binding['dataset_doi']):
        errors.append('Catalog source binding differs from the imported dataset.')
    controls=spec['controls']
    ids=[c['id'] for c in controls]
    if len(ids)!=len(set(ids)):errors.append('Duplicate control IDs.')
    primary={c['id'] for c in controls if c['tier']=='primary'}
    if primary!={'3ftx','pla2','svmp','svsp'}:errors.append('Primary controls differ from the documented contract.')
    evidence_ids={c['id'] for c in evidence['claims']}
    source_ids={s['id'] for s in evidence['sources']}
    if len(evidence_ids)!=len(evidence['claims']):errors.append('Duplicate evidence IDs.')
    bound=[]
    for control in controls:
        for field in ['definition','boundaries','interpretation','design_role']:
            if not control.get(field):errors.append(f'{control["id"]}: missing {field}.')
        if not control.get('evidence_ids'):errors.append(f'{control["id"]}: no evidence locators.')
        for eid in control.get('evidence_ids',[]):
            if eid not in evidence_ids:errors.append(f'Unresolved evidence ID: {eid}.')
        for tid in control['source_toxin_ids']:
            bound.append(tid)
            row=conn.execute('SELECT canonical_id,original_label FROM toxin_dictionary WHERE toxin_id=?',(tid,)).fetchone()
            if row is None or row[0]!=control['id'] or row[1]!=control['short_label']:
                errors.append(f'{control["id"]}: mismatched source binding {tid}.')
    if len(bound)!=len(set(bound)):errors.append('A source category is bound to multiple controls.')
    for claim in evidence['claims']:
        if claim['source_id'] not in source_ids:errors.append(f'Unresolved evidence source: {claim["id"]}.')
        if not claim.get('limits') or not claim.get('locator'):errors.append(f'Missing evidence context: {claim["id"]}.')
    for source in evidence['sources']:
        if not (ROOT/source['local_path']).is_file():errors.append(f'Missing local source {source["id"]}.')
    policy=spec['phenotype_policy']
    if policy['direct_percentage_to_anatomy_rules']:errors.append('Unreviewed direct anatomy rules must not be introduced.')
    if not all(policy[k] for k in ['require_citation_for_documented_traits','require_reference_species_for_documented_traits','require_creative_label_when_no_trait_evidence']):
        errors.append('Trait provenance requirements disabled.')
    return errors

def main():
    spec=json.loads((ROOT/'config/venom_input_spec.json').read_text())
    evidence=json.loads((ROOT/'evidence/input_evidence.json').read_text())
    schema=json.loads((ROOT/'schemas/snake_concept.schema.json').read_text())
    database=ROOT/'data/processed/venom_diet_2023/serpentshaper.sqlite'
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as conn:
        errors=validate_spec(spec,evidence,conn)
        # Check the documented examples directly, without estimating associations.
        for row,name,tid,value in [(286,'Naja naja','vd2023_E',96.9),(306,'Oxyuranus scutellatus','vd2023_T',79.4),
                                   (191,'Dispholidus typus','vd2023_AZ',77.5),(299,'Ovophis convictus','vd2023_BG',52.94),
                                   (189,'Dendroaspis polylepis','vd2023_Z',61.1)]:
            found=conn.execute('''SELECT p.species_name,c.abundance_pct,p.ingestion_status,p.measurement_type
              FROM profiles p JOIN components c USING(profile_id) WHERE p.source_row=? AND c.toxin_id=?''',(row,tid)).fetchone()
            if found!=(name,value,'ready_with_caveats','proteomics'):errors.append(f'Documented example differs from source row {row}.')
    # Verify named source section anchors for the main study.
    article=ET.parse(ROOT/'sources/PMC9744630.xml').getroot()
    anchors={s.get('id') for s in article.iter('sec')}
    for anchor in ['sec1','sec3-2','sec3-3','sec3-5','sec3-6','sec3-7','sec2-5-1','sec2-5-2']:
        if anchor not in anchors:errors.append(f'Missing evidence locator {anchor}.')
    result={'status':'failed' if errors else 'passed','controls':len(spec['controls']),
            'primary_controls':sum(c['tier']=='primary' for c in spec['controls']),
            'advanced_controls':sum(c['tier']=='advanced' for c in spec['controls']),
            'seed_evidence_records':len(evidence['claims']), 'documented_examples_verified':5,
            'schema_check':'JSON syntax only; standards-compliant JSON Schema runtime validation is not integrated',
            'errors':errors}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()

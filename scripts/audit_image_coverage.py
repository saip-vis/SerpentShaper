"""Provisional exact-name overlap of venom records and mirrored SnakeCLEF metadata."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[1]

def main():
    metadata=ROOT/'sources/image_research'
    rows_by_name=defaultdict(set)
    observations=defaultdict(set)
    splits=defaultdict(lambda:defaultdict(set))
    files=[]
    for path in sorted(metadata.glob('SnakeCLEF*.csv')):
        provider='herpmapper' if '-HM.' in path.name else 'inaturalist'
        count=0
        with path.open(newline='',encoding='utf-8-sig') as f:
            reader=csv.DictReader(f)
            fields=reader.fieldnames
            for row in reader:
                name=' '.join(row['binomial_name'].replace('_',' ').split())
                key=(provider,row['image_path'])
                rows_by_name[name].add(key)
                observations[name].add((provider,row['observation_id']))
                splits[name][row['subset']].add(key)
                count+=1
        files.append({'name':path.name,'rows':count,'columns':fields})
    with (ROOT/'data/raw/museum_venomics/PublishedProteomes.csv').open() as f:
        published={' '.join(r['Species2'].replace('_',' ').split()) for r in csv.DictReader(f)}
    database=ROOT/'data/processed/venom_diet_2023/serpentshaper.sqlite'
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as conn:
        eligible={r[0] for r in conn.execute('SELECT DISTINCT species_name FROM ready_proteomic_profiles')}
    def coverage(names):
        return {'venom_taxon_labels':len(names), 'exact_name_matches':len(names & rows_by_name.keys()),
                'unmatched_names':sorted(names-rows_by_name.keys()),
                'metadata_image_records_for_matched_names':sum(len(rows_by_name[n]) for n in names),
                'taxa':[{'venom_name':name,'metadata_image_records':len(rows_by_name[name]),
                         'metadata_observations':len(observations[name]),
                         'by_subset':{s:len(v) for s,v in splits[name].items()}}
                        for name in sorted(names)]}
    result={'status':'provisional_metadata_only','research_date':'2026-11-18',
        'official_source':'https://www.imageclef.org/node/319',
        'download_source':'https://huggingface.co/pengdadaaa/SnakeCLEF2024/tree/main/metadata',
        'mirror_commit':json.loads((metadata/'snakeclef_participant_repo.json').read_text())['sha'],
        'metadata_files':files,'distinct_metadata_species_names':len(rows_by_name),
        'eligible_proteomic_profiles':coverage(eligible),'published_compilation':coverage(published),
        'limitations':['Exact-name matches only; synonyms/subspecies and taxonomy changes are not resolved.',
            'Image existence, quality, viewpoint and reuse permission are not verified by metadata matches.',
            'No viewing-angle, photographer or photo-license columns occur in these metadata CSVs.',
            'Participant mirror has not been byte-compared to the official downloads, which failed certificate verification.',
            'SnakeCLEF reuses iNaturalist images; treat sources as overlapping rather than additive.']}
    (ROOT/'reports/image_research/coverage_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['eligible_proteomic_profiles','published_compilation']},indent=2))
    for key in ['eligible_proteomic_profiles','published_compilation']:
        print(key,{k:v for k,v in result[key].items() if k!='taxa'})
    print('reference examples',[x for x in result['eligible_proteomic_profiles']['taxa'] if x['venom_name'] in
        ['Naja naja','Oxyuranus scutellatus','Dispholidus typus','Dendroaspis polylepis','Ovophis convictus']])

if __name__=='__main__':main()

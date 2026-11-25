"""Prepare a small, diverse review shortlist without changing photo decisions."""
import argparse
import json
from pathlib import Path
from build_image_triage_queue import build
from build_learned_training_data import ROOT

OUT=ROOT/'ML/image_traits/photo_pilot_review_shortlist.json'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--species',type=int,default=16,help='Maximum number of source labels')
    parser.add_argument('--per-species',type=int,default=2,help='Maximum candidate images per label')
    args=parser.parse_args()
    if not 1<=args.species<=30 or not 1<=args.per_species<=3:parser.error('Limits: 1–30 species and 1–3 images per species')
    result=build(max_species=args.species,per_species=args.per_species)
    result['purpose']='Prioritize a small visual review batch; no identity, health, trait or license validation is implied.'
    result['next_step']='Inspect each original image and provider page for visible traits, identity and condition before recording any acceptance or label.'
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'source_species_count':result['source_species_count'],'image_count':result['image_count'],'output':str(OUT.relative_to(ROOT))}))

if __name__=='__main__':main()

"""Make local-only, labeled contact sheets for assistant-supported visual triage."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw
from build_learned_training_data import ROOT

QUEUE=ROOT/'ML/learned_morphology/image_triage_queue.json'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',default='/private/tmp/serpentshaper_image_triage');args=parser.parse_args()
    destination=Path(args.output_dir);destination.mkdir(parents=True,exist_ok=True)
    source=json.loads(QUEUE.read_text());species=source['species'];pages=[]
    for page in range(0,len(species),4):
        selected=species[page:page+4];canvas=Image.new('RGB',(1500,len(selected)*370),'white');draw=ImageDraw.Draw(canvas)
        for row,entry in enumerate(selected):
            draw.text((8,row*370+3),entry['species_label']+' — unreviewed; triage only',fill='black')
            for col,photo in enumerate(entry['images']):
                path=(ROOT/photo['local_path']).resolve()
                if not path.is_relative_to(ROOT.resolve()) or not path.is_file():raise ValueError('Image missing or outside repository')
                with Image.open(path) as original:
                    im=original.convert('RGB');im.thumbnail((485,320))
                    x=col*500+(485-im.width)//2;y=row*370+25+(320-im.height)//2;canvas.paste(im,(x,y))
                draw.text((col*500+4,row*370+349),photo['image_id']+'  obs '+str(photo['observation_id']),fill='black')
        path=destination/f'triage_{page//4+1:02d}.jpg';canvas.save(path,quality=85);pages.append(str(path))
    print('\n'.join(pages))


if __name__=='__main__':main()

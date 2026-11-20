"""Build local review pages and numbered contact sheets (requires Pillow)."""
import argparse
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', default='pilot_001_spectacled_cobra')
    args = parser.parse_args()
    if Path(args.batch).name != args.batch or args.batch in ('.', '..'):
        parser.error('Choose a batch folder name.')
    folder = ROOT / 'data/image_pilots' / args.batch
    rows = json.loads((folder / 'manifest.json').read_text())
    page = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>SerpentShaper image review</title>',
            '<style>body{font:16px system-ui;max-width:1100px;margin:30px auto;padding:20px;background:#f4f5f7}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}article{background:white;padding:18px;border-radius:12px}img{width:100%;height:300px;object-fit:contain}small{display:block;overflow-wrap:anywhere}a{color:#175ba0}</style>',
            '<h1>SerpentShaper: image candidates</h1><p>Provider labels are provisional. Review species identity, framing, visibility, coloration, and duplicates. IDs remain stable within this batch. Multiple photos may show the same snake; observation IDs are not independent specimens.</p>']
    for species in dict.fromkeys(r['source_species_name'] for r in rows):
        group = [r for r in rows if r['source_species_name'] == species]
        prefix = {'Naja naja':'SC', 'Oxyuranus scutellatus':'TA', 'Dendroaspis polylepis':'BM',
                  'Crotalus atrox':'WD', 'Bitis arietans':'PA', 'Bothrops jararaca':'JA',
                  'Dispholidus typus':'BO', 'Aipysurus laevis':'OS', 'Bitis gabonica':'GV'}.get(species, species.replace(' ', '_'))
        sheet = Image.new('RGB', (1000, 80 + 280 * ((len(group)+1)//2)), '#f4f5f7')
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 15), species + ' | provider-labelled, awaiting review', fill='black', font_size=21)
        draw.text((20, 45), f'{prefix} IDs follow manifest order. Multiple images may share one observation.', fill='black', font_size=15)
        page += ['<h2>' + html.escape(species) + '</h2><section>']
        for i, row in enumerate(group):
            rid = f'{prefix}{i+1:02d}'
            row['review_id'] = rid
            x, y = (i % 2)*500, 80+(i//2)*280
            draw.rectangle((x+5,y+5,x+495,y+275), fill='white')
            relative = row.get('local_path')
            if row.get('download_status') == 'downloaded' and relative:
                path = (folder / relative).resolve()
                if not path.is_relative_to(folder.resolve()):
                    raise ValueError('Image path outside batch')
                with Image.open(path) as image:
                    thumb = ImageOps.exif_transpose(image).convert('RGB')
                    thumb.thumbnail((480, 215))
                    sheet.paste(thumb,(x+10+(480-thumb.width)//2,y+10+(215-thumb.height)//2))
                src = html.escape(relative, quote=True)
                photo_html = f'<a href="{src}"><img src="{src}" alt="{rid}"></a>'
            else:
                photo_html = '<p>Image not downloaded.</p>'
            draw.text((x+15,y+230), f"{rid} | photo {row['image_id']} | observation {row['observation_id']}", fill='black', font_size=14)
            draw.text((x+15,y+251), 'Status: ' + row['review_status'], fill='#555555', font_size=13)
            page += [f'<article><h3>{rid}</h3>{photo_html}<p>Observation: {row["observation_id"]}</p>',
                     '<p>Status: '+html.escape(row['review_status'])+'</p>',
                     '<p>Rendering exclusion: '+html.escape(row.get('rendering_exclusion_reason', 'none recorded; acceptance still required'))+'</p>',
                     '<p>'+('Exact duplicate: '+html.escape(str(row['duplicate_of'])) if row.get('duplicate_of') else '')+'</p>',
                     '<p>Suitability: '+html.escape(row.get('suitability_screening', {}).get('category', 'not_screened'))+
                     ' — '+html.escape(row.get('suitability_screening', {}).get('reason', 'Pending screening.'))+'</p>',
                     '<p>'+html.escape(row.get('assistant_visual_review', {}).get('notes', 'Awaiting visual review.'))+'</p>',
                     f'<a href="{html.escape(row["source_page"],quote=True)}">Original observation</a> | <a href="{html.escape(row["photo_page"],quote=True)}">Photo and license</a>',
                     '<small>'+html.escape(row.get('attribution') or 'Attribution unknown')+'</small>',
                     '<small>License: '+html.escape(row['photo_license'])+'; framing/view/pose unreviewed</small>',
                     '<small>Filename: '+html.escape(relative or 'None')+'</small></article>']
        page += ['</section>']
        sheet.save(folder / (prefix + '_contact_sheet.jpg'), quality=93)
    page += ['</html>']
    (folder / 'review.html').write_text('\n'.join(page))
    (folder / 'manifest.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(folder / 'review.html')

if __name__ == '__main__':
    main()

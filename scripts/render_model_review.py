"""Raster review plates from the actual editable SVG previews; original photos are untouched.
Run after build-preview-gallery.cjs. Requires Pillow and rsvg-convert.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
def main():
    presets = json.loads((ROOT/'PhysicalRendererTest/presets/species-presets.json').read_text())['presets']
    preview = ROOT/'PhysicalRendererTest/preset-previews'
    out = ROOT/'PhysicalRendererTest/visual-studies/catalog-modeling'
    out.mkdir(exist_ok=True)
    for page, start in enumerate(range(0, len(presets), 6), 1):
        plate = Image.new('RGB', (1400, 1140), '#f7f9f5')
        draw = ImageDraw.Draw(plate)
        draw.text((16, 8), 'SerpentShaper: illustrative drafts, not validated anatomy or measurements', fill='#243b31')
        for i, p in enumerate(presets[start:start+6]):
            x, y = (i % 2)*700, (i//2)*370+25
            draw.text((x+12, y+8), f"{p['source_species_name']} | revision {p['model_revision']}", fill='#243b31')
            with tempfile.TemporaryDirectory() as temp:
                for suffix,w,h,dx,dy in [('',350,300,0,35),('-head',340,210,350,65)]:
                    target=Path(temp)/(p['preset_id']+suffix+'.png')
                    # Specifying both dimensions stretches SVGs with no explicit
                    # intrinsic size, distorting anatomy during visual review.
                    subprocess.run(['rsvg-convert','-w',str(w),str(preview/(p['preset_id']+suffix+'.svg')),'-o',str(target)],check=True)
                    image=Image.open(target).convert('RGBA')
                    image.thumbnail((w,h), Image.Resampling.LANCZOS)
                    plate.paste(image,(x+dx,y+dy),image)
        plate.save(out/f'plate_{page:02}.png')
    print(f'Wrote {(len(presets)+5)//6} review plates from {len(presets)} actual SVG models.')
if __name__=='__main__':
    main()

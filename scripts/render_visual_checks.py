"""Render local comparison sheets from the reproducible SVG validation run.

Requires Pillow and rsvg-convert. Reference drawings are authored project SVGs,
not source photographs. No downloaded photographs are copied to the report.
"""
import io
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/visual_generation_checks'
WORK = OUT / '.work'


def font(size, bold=False):
    name = 'Arial Bold.ttf' if bold else 'Arial.ttf'
    try:
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/' + name, size)
    except OSError:
        return ImageFont.load_default()


def render(filename, width, height):
    binary = shutil.which('rsvg-convert')
    if not binary:
        raise RuntimeError('rsvg-convert is required to render the SVG comparison sheets')
    result = subprocess.run([binary, '--background-color', '#ffffff', '-w', str(width), '-h', str(height),
                             str(WORK / filename)], capture_output=True, check=True)
    with Image.open(io.BytesIO(result.stdout)) as im:
        result = im.convert('RGB')
        result.thumbnail((width, height))
        return result


def main():
    data = json.loads((OUT / 'results.json').read_text())
    canvas = Image.new('RGB', (1440, 1750), '#f4f7f3')
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 20), 'SerpentShaper: reference and generated concepts', fill='#173c2a', font=font(29, True))
    draw.text((30, 60), 'Reference drawings are authored illustrations; these venom profiles were used for training.', fill='#50675a', font=font(17))
    draw.text((30, 85), 'Control values are illustration settings, not probabilities or measured anatomy.', fill='#50675a', font=font(17))
    for index, case in enumerate(data['cases']):
        x, y = 25 + (index % 2) * 710, 120 + (index // 2) * 400
        draw.rounded_rectangle((x, y, x+690, y+380), 12, fill='white', outline='#dae5d9')
        common = case['common_name'] or case['species']
        title = f"{common}  |  {case['species']}"
        draw.text((x+14, y+11), title, fill='#203d2c', font=font(18, True))
        draw.text((x+14, y+38), f"Source row {case['source_row']} · authored reference", fill='#728578', font=font(14))
        draw.text((x+354, y+38), 'Generated from the same inputs', fill='#728578', font=font(14))
        for side, key in enumerate(('reference_svg', 'generated_svg')):
            im = render(case[key], 330, 270)
            xx, yy = x + 10 + side * 340, y + 60
            canvas.paste(im, (xx + (330-im.width)//2, yy + (270-im.height)//2))
        t = case['predicted']
        draw.text((x+14, y+341), f"Controls: hood {t['hood']:.2f}  ·  bands {t['bands']:.2f}  ·  diamonds {t['diamond']:.2f}  ·  rattle {t['rattle']:.2f}", fill='#59705f', font=font(14))
    canvas.save(OUT / 'comparison.png', optimize=True)

    strip = Image.new('RGB', (1500, 450), '#f4f7f3')
    draw = ImageDraw.Draw(strip)
    draw.text((25, 15), 'One possible interpolation between two input profiles', fill='#173c2a', font=font(25, True))
    draw.text((25, 49), 'Missing entries set to zero for this exercise; the intermediate snake has no known correct appearance.', fill='#50675a', font=font(15))
    for index, fraction in enumerate((0, 25, 50, 75, 100)):
        x = index * 295 + 18
        title = f'{fraction}% toward cobra profile'
        draw.text((x, 78), title, fill='#203d2c', font=font(15, True))
        im = render(f'transition_{fraction}.svg', 280, 300)
        strip.paste(im, (x + (280-im.width)//2, 108 + (300-im.height)//2))
    strip.save(OUT / 'transition.png', optimize=True)
    print('Wrote comparison.png and transition.png; original photographs were not copied.')


if __name__ == '__main__':
    main()

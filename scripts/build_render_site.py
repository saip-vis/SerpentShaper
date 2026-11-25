#!/usr/bin/env python3
"""Build the public, browser-only SerpentShaper site for Render."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / 'render-dist'
MARKER = '.serpentshaper-static-build'
PAGES = ('MainInterface/home.html', 'MainInterface/index.html', 'MainInterface/about.html')
ASSETS = ('MainInterface/assets/forest-background.png', 'MainInterface/assets/cobra-foreground.png')
ALLOWED_DIRS = (ROOT / 'MainInterface', ROOT / 'PhysicalRendererTest')
ALLOWED_EXTENSIONS = {'.js', '.css', '.png'}


class Dependencies(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'):
            self.paths.append(attrs['src'])
        elif tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs.get('href'):
            self.paths.append(attrs['href'])


def collect_files():
    files = {ROOT / page for page in PAGES} | {ROOT / asset for asset in ASSETS}
    for page in PAGES:
        source = ROOT / page
        parser = Dependencies()
        parser.feed(source.read_text(encoding='utf-8'))
        for url in parser.paths:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or parsed.path.startswith('/'):
                raise ValueError(f'Unexpected external or absolute dependency in {page}: {url}')
            resolved = (source.parent / unquote(parsed.path)).resolve()
            if not any(resolved.is_relative_to(base) for base in ALLOWED_DIRS):
                raise ValueError(f'Dependency outside public asset directories: {url}')
            if resolved.suffix.lower() not in ALLOWED_EXTENSIONS or not resolved.is_file():
                raise ValueError(f'Missing or unsupported dependency: {url}')
            files.add(resolved)
    for source in files:
        if not source.is_file():
            raise ValueError(f'Missing public file: {source.relative_to(ROOT)}')
    return files


def build(destination=DESTINATION):
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError('Refusing to replace a symbolic link')
    if destination.exists() and not (destination / MARKER).is_file():
        raise ValueError(f'Refusing to replace a directory not created by this build: {destination}')
    files = collect_files()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.serpentshaper-static-', dir=destination.parent) as tmp:
        stage = Path(tmp) / 'site'
        stage.mkdir()
        for source in files:
            target = stage / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (stage / 'index.html').write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="refresh" content="0;url=MainInterface/home.html">'
            '<title>SerpentShaper</title></head><body>'
            '<p>Continue to <a href="MainInterface/home.html">SerpentShaper</a>.</p>'
            '</body></html>\n', encoding='utf-8')
        (stage / MARKER).write_text('Generated static site.\n', encoding='utf-8')
        if destination.exists():
            shutil.rmtree(destination)
        stage.replace(destination)
    print(f'Built {len(files)} public files in {destination}')


if __name__ == '__main__':
    build()

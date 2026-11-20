"""Build a local index of species folders and download outcomes."""
from collections import Counter
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    base = ROOT / 'data/image_pilots'
    progress_path = ROOT / 'reports/image_research/remaining_species_downloads/progress.json'
    progress = json.loads(progress_path.read_text()) if progress_path.exists() else {'species': {}}
    rows = []
    totals = Counter()
    for folder in sorted(base.glob('pilot_*')):
        path = folder / 'manifest.json'
        if not path.exists():
            continue
        records = json.loads(path.read_text())
        names = {r['source_species_name'] for r in records}
        if len(names) > 1:
            raise ValueError('Mixed species folder: '+folder.name)
        species = next(iter(names)) if names else next((name for name, r in progress['species'].items() if r['batch']==folder.name), 'No resolved species')
        counts = Counter(r['review_status'] for r in records)
        downloaded = sum(r.get('download_status')=='downloaded' for r in records)
        totals.update(files=downloaded, accepted=counts['accepted'], rejected=counts['rejected'], pending=counts['unreviewed'])
        result = progress['species'].get(species, {})
        outcome = result.get('status', 'earlier pilot' if int(folder.name.split('_')[1]) <= 9 else 'in progress')
        note = result.get('notes', '')
        link = f'<a href="{html.escape(folder.name, quote=True)}/review.html">Review gallery</a>' if (folder/'review.html').exists() else 'No gallery'
        rows.append(f'<tr><td>{html.escape(folder.name)}</td><td><i>{html.escape(species)}</i></td><td>{downloaded}</td><td>{counts["accepted"]}</td><td>{counts["rejected"]}</td><td>{html.escape(outcome)}</td><td>{link}</td><td>{html.escape(note)}</td></tr>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SerpentShaper collection index</title><style>body{font:15px system-ui;margin:30px;color:#172b23;background:#f5f7f5}h1{font-size:28px}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #d9e2dd;vertical-align:top}th{background:#dce8df}a{color:#155c37}.scroll{overflow-x:auto}td:last-child{min-width:260px}input{padding:12px;font:inherit;width:min(550px,90%);margin-bottom:20px}</style>
<h1>SerpentShaper image collection</h1>'''
    page += f'<p>{len(rows)} species folders | {totals["files"]} downloaded files | {totals["accepted"]} marked accepted | {totals["rejected"]} rejected.</p>'
    page += '<p>Downloaded files include rejected and unreviewed material. Species labels are provisional until reviewed. New batches remain excluded from rendering training. Skips describe the bounded provider search, not absence of photographs everywhere.</p>'
    page += '<p><a href="../../reports/image_research/remaining_species_downloads/post_download_notes.md">Post-download notes</a></p>'
    page += '<input id="filter" aria-label="Filter species or folders" placeholder="Filter species, folder, or outcome"><div class="scroll"><table><thead><tr><th>Folder</th><th>Species label</th><th>Downloaded</th><th>Accepted</th><th>Rejected</th><th>Collection outcome</th><th>Review</th><th>Notes</th></tr></thead><tbody>'
    page += '\n'.join(rows)
    page += '''</tbody></table></div><script>document.getElementById('filter').addEventListener('input', event => {const q=event.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(row=>{row.hidden=!row.textContent.toLowerCase().includes(q);});});</script></html>'''
    (base / 'index.html').write_text(page)
    print(f'Indexed {len(rows)} folders, {totals["files"]} files: {base / "index.html"}')

if __name__ == '__main__':
    main()

"""Local image curation server. Run ./start_image_review.sh, then open port 8767."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import threading
from urllib.parse import parse_qs, urlsplit

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / 'data/image_pilots'
FIELDS = ('review_status', 'rendering_training_excluded', 'rendering_exclusion_reason',
          'reference_only_exception', 'suitability_screening', 'human_review', 'framing',
          'viewpoint', 'pose', 'body_condition', 'species_confidence', 'review_notes', 'review_issues')
OPTIONS = {
    'species_confidence': ['unknown', 'likely', 'confirmed', 'uncertain'],
    'body_condition': ['unknown', 'no_visible_injury', 'injured', 'deformed', 'uncertain'],
    'framing': ['unknown', 'full_body', 'head', 'partial_body', 'detail', 'multiple', 'not_snake'],
    'viewpoint': ['unknown', 'dorsal', 'lateral', 'ventral', 'front', 'oblique'],
    'pose': ['unknown', 'coiled', 'extended', 'raised', 'swimming', 'handled'],
}
ISSUES = {'injury', 'deformation', 'heavy_occlusion', 'handling', 'severe_blur', 'not_snake', 'duplicate'}
COMMON = {'Naja naja': 'Spectacled cobra', 'Oxyuranus scutellatus': 'Coastal taipan',
          'Dendroaspis polylepis': 'Black mamba', 'Crotalus atrox': 'Western diamondback',
          'Bitis arietans': 'Puff adder', 'Bothrops jararaca': 'Jararaca',
          'Dispholidus typus': 'Boomslang', 'Aipysurus laevis': 'Olive sea snake',
          'Bitis gabonica': 'Gaboon viper'}
Image.MAX_IMAGE_PIXELS = 160_000_000

class ReviewError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

def revision(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def injury_locked(row):
    return (row.get('rendering_exclusion_reason') == 'injury'
            or row.get('body_condition') in {'injured', 'deformed'}
            or bool({'injury', 'deformation'} & set(row.get('review_issues', []))))

def is_eligible(row):
    # Shared with the ingestion export; never infer acceptance from a download.
    from scripts.export_rendering_manifest import eligible
    return eligible(row)

class ReviewStore:
    def __init__(self, data_root=DEFAULT_DATA):
        self.root = Path(data_root).resolve()
        self.lock = threading.RLock()
        self.preview_lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)
        self.notes = {}
        report = ROOT / 'reports/image_research/remaining_species_downloads/progress.json'
        if self.root == DEFAULT_DATA.resolve() and report.exists():
            self.notes = {r['batch']: r for r in json.loads(report.read_text())['species'].values()}

    def batch_folder(self, batch):
        if not isinstance(batch, str) or not re.fullmatch(r'pilot_\d{3}_[A-Za-z0-9_]+', batch):
            raise ReviewError('Invalid species folder.')
        folder = (self.root / batch).resolve()
        if not folder.is_relative_to(self.root) or not (folder / 'manifest.json').is_file():
            raise ReviewError('Species folder not found.', 404)
        return folder

    def read(self, batch):
        return json.loads((self.batch_folder(batch) / 'manifest.json').read_text())

    def find(self, batch, image_id):
        rows = self.read(batch)
        for row in rows:
            if row['image_id'] == image_id:
                return rows, row
        raise ReviewError('Image record not found.', 404)

    def original(self, batch, row):
        if row.get('download_status') != 'downloaded' or not row.get('local_path'):
            raise ReviewError('This image was not downloaded.', 404)
        folder = self.batch_folder(batch)
        path = (folder / row['local_path']).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise ReviewError('Image path is missing or outside its species folder.', 404)
        return path

    def detail(self, batch, image_id):
        with self.lock:
            _, row = self.find(batch, image_id)
            result = deepcopy(row)
            result.update(revision=revision(row), injury_locked=injury_locked(row),
                          eligible_for_rendering=is_eligible(row),
                          can_undo=bool(row.get('review_history') and
                              row['review_history'][-1].get('source') == 'image_review_interface' and
                              row['review_history'][-1].get('action') == 'review'))
            return result

    def catalog(self):
        with self.lock:
            batches, all_counts = [], Counter()
            for path in sorted(self.root.glob('pilot_*/manifest.json')):
                batch = path.parent.name
                rows = self.read(batch)
                counts = Counter(r.get('review_status', 'unreviewed') for r in rows if r.get('download_status') == 'downloaded')
                all_counts.update(counts)
                species = rows[0]['source_species_name'] if rows else self.notes.get(batch, {}).get('species', batch)
                batches.append(dict(batch=batch, species=species, common_name=COMMON.get(species, ''),
                    counts=dict(counts), total=sum(counts.values()),
                    eligible=sum(is_eligible(r) for r in rows), collection_note=self.notes.get(batch, {}).get('notes', '')))
            return dict(batches=batches, counts=dict(all_counts), total=sum(all_counts.values()),
                        token=self.token, test_workspace=self.root != DEFAULT_DATA.resolve())

    def images(self, batch, status='all'):
        if status not in {'all', 'unreviewed', 'accepted', 'rejected', 'needs_review', 'reference_only'}:
            raise ReviewError('Unknown review filter.')
        with self.lock:
            return [dict(image_id=r['image_id'], review_id=r.get('review_id', r['image_id']),
                         review_status=r.get('review_status', 'unreviewed'), observation_id=r['observation_id'],
                         duplicate=bool(r.get('duplicate_of')), excluded=bool(r.get('rendering_training_excluded')))
                    for r in self.read(batch) if r.get('download_status') == 'downloaded'
                    and (status == 'all' or r.get('review_status', 'unreviewed') == status)]

    def update(self, payload):
        if not isinstance(payload, dict):
            raise ReviewError('Expected a JSON object.')
        batch, image_id = payload.get('batch'), payload.get('image_id')
        with self.lock:
            rows, row = self.find(batch, image_id)
            if payload.get('revision') != revision(row):
                raise ReviewError('This record changed since you opened it. Reload it before saving.', 409)
            previous = {key: deepcopy(row[key]) for key in FIELDS if key in row}
            action = payload.get('action', 'review')
            if action == 'undo':
                history = row.get('review_history', [])
                if not history or history[-1].get('source') != 'image_review_interface' or history[-1].get('action') != 'review':
                    raise ReviewError('There is no interface review to undo for this image.')
                restore = deepcopy(history[-1]['before'])
                for key in FIELDS:
                    row.pop(key, None)
                row.update(restore)
            elif action == 'review':
                self.apply_review(row, payload)
            else:
                raise ReviewError('Unknown action.')
            row.setdefault('review_history', []).append(dict(source='image_review_interface', action=action,
                reviewed_at=timestamp(), reviewer='user', before=previous,
                after={key: deepcopy(row[key]) for key in FIELDS if key in row}))
            # Save an exact pre-write manifest backup, including original provenance.
            original = self.batch_folder(batch) / 'manifest.json'
            backup = self.root / '_review_backups' / batch
            backup.mkdir(parents=True, exist_ok=True)
            (backup / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + secrets.token_hex(6) + '.json')).write_bytes(original.read_bytes())
            atomic_json(original, rows)
            self.export()
            return self.detail(batch, image_id)

    def apply_review(self, row, payload):
        decision = payload.get('decision')
        if decision not in {'accept', 'reject', 'flag', 'reference'}:
            raise ReviewError('Choose accept, reject, flag, or reference.')
        values = {key: payload.get(key, 'unknown') for key in OPTIONS}
        for key, value in values.items():
            if value not in OPTIONS[key]:
                raise ReviewError(f'Invalid {key}.')
        issues = payload.get('issues', [])
        if not isinstance(issues, list) or any(not isinstance(v, str) or v not in ISSUES for v in issues):
            raise ReviewError('Invalid image issue.')
        issues = sorted(set(issues))
        notes = payload.get('notes', '')
        if not isinstance(notes, str) or len(notes) > 4000:
            raise ReviewError('Notes must be text, up to 4,000 characters.')
        notes = notes.strip()
        known_injury = injury_locked(row)
        injured = known_injury or values['body_condition'] in {'injured', 'deformed'} or bool({'injury','deformation'} & set(issues))
        if decision == 'accept':
            if injured or row.get('reference_only_exception'):
                raise ReviewError('An injury/deformity exclusion cannot be accepted for rendering. Reject it or document a unique reference-only use.')
            if row.get('duplicate_of') or issues:
                raise ReviewError('Resolve image issues first. Exact duplicate copies stay excluded; use the original record.')
            if values['species_confidence'] != 'confirmed' or values['body_condition'] != 'no_visible_injury':
                raise ReviewError('Accept requires confirmed species identity and an explicit no-visible-injury assessment.')
            if values['framing'] in {'unknown', 'not_snake', 'multiple'}:
                raise ReviewError('Choose a useful single-snake framing before accepting.')
        if decision in {'reject', 'flag'} and not notes and not issues:
            raise ReviewError('Add a note or select an issue to explain this decision.')
        if decision == 'reference' and not notes:
            raise ReviewError('Explain which anatomy makes this a useful reference.')
        if decision == 'reference' and injured and payload.get('unique_reference') is not True:
            raise ReviewError('An injured reference requires confirmation that its anatomy is uniquely useful and unavailable in healthy alternatives.')
        row.update(values)
        # Preserve the known injury even if a later reference/flag form says unknown.
        if injured and row['body_condition'] not in {'injured','deformed'}:
            row['body_condition'] = 'injured'
        row['species_confidence'] = values['species_confidence']
        row['review_issues'], row['review_notes'] = issues, notes
        status = {'accept':'accepted', 'reject':'rejected', 'flag':'needs_review', 'reference':'reference_only'}[decision]
        row['review_status'] = status
        row['human_review'] = dict(reviewer='user', reviewed_at=timestamp(), decision=decision,
                                  species_confidence=values['species_confidence'], body_condition=row['body_condition'],
                                  issues=issues, notes=notes, unique_reference=payload.get('unique_reference') is True)
        row['reference_only_exception'] = bool(decision == 'reference' and injured)
        row['rendering_training_excluded'] = decision != 'accept'
        if decision == 'accept':
            row.pop('rendering_exclusion_reason', None)
        else:
            row['rendering_exclusion_reason'] = ('injury' if injured else
                'exact_duplicate' if row.get('duplicate_of') else
                'reference_only' if decision == 'reference' else
                'rejected_by_user' if decision == 'reject' else 'pending_visual_review')
        row['suitability_screening'] = dict(reviewer='user', reviewed_on=timestamp(),
            category='candidate' if decision == 'accept' else 'supplemental' if decision == 'reference' else
            'rejected' if decision == 'reject' else 'pending', reason=notes or ', '.join(issues) or 'User accepted after visual review.')

    def preview(self, batch, image_id, size):
        if size not in {'thumb', 'preview'}:
            raise ReviewError('Unknown preview size.')
        with self.lock:
            _, row = self.find(batch, image_id)
            path = self.original(batch, row)
            key = hashlib.sha256(f'{batch}:{image_id}:{row.get("sha256")}:{path.stat().st_mtime_ns}:{size}'.encode()).hexdigest()
        folder = self.root / '_review_previews' / batch
        cached = folder / (key + '.jpg')
        with self.preview_lock:
            if not cached.exists():
                limit = 320 if size == 'thumb' else 1600
                with Image.open(path) as image:
                    if image.width * image.height > 160_000_000:
                        raise ReviewError('Original exceeds the preview size limit; inspect it separately.', 422)
                    image.draft('RGB', (limit, limit))
                    view = ImageOps.exif_transpose(image).convert('RGB')
                    view.thumbnail((limit, limit), Image.Resampling.LANCZOS)
                    folder.mkdir(parents=True, exist_ok=True)
                    temporary = cached.with_suffix('.tmp')
                    view.save(temporary, format='JPEG', quality=87)
                    temporary.replace(cached)
        return cached

    def export(self):
        with self.lock:
            records = []
            for manifest in sorted(self.root.glob('pilot_*/manifest.json')):
                for row in self.read(manifest.parent.name):
                    if is_eligible(row):
                        path = self.original(manifest.parent.name, row)
                        records.append(dict(row, batch=manifest.parent.name,
                            local_path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)))
            atomic_json(self.root / 'rendering_manifest.json', dict(policy='config/image_review_policy.json',
                note='Explicit accepted reviews only; excluded, duplicate, and reference-only records omitted.', images=records))
            return {'exported': len(records), 'file': 'rendering_manifest.json'}

def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body, status=200, mime='application/json', cache='no-store'):
            data = json.dumps(body).encode() if mime == 'application/json' else body
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', cache)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers()
            self.wfile.write(data)

        def host_check(self):
            host = urlsplit('http://' + self.headers.get('Host', '')).hostname
            if host not in {'127.0.0.1', 'localhost'}:
                raise ReviewError('Local access only.', 403)

        def do_GET(self):
            try:
                self.host_check()
                parsed = urlsplit(self.path)
                query = {k:v[0] for k,v in parse_qs(parsed.query).items()}
                path = parsed.path
                if path == '/':
                    self.send((ROOT / 'ImageReview.html').read_bytes(), mime='text/html; charset=utf-8')
                elif path == '/api/catalog':
                    self.send(store.catalog())
                elif path == '/api/images':
                    self.send(store.images(query.get('batch'), query.get('status','all')))
                elif path == '/api/image':
                    self.send(store.detail(query.get('batch'), query.get('image_id')))
                elif path == '/media':
                    preview = store.preview(query.get('batch'), query.get('image_id'), query.get('size','preview'))
                    self.send(preview.read_bytes(), mime='image/jpeg', cache='private, max-age=86400')
                elif path == '/original':
                    with store.lock:
                        _, row = store.find(query.get('batch'), query.get('image_id'))
                        original = store.original(query.get('batch'), row)
                        self.send(original.read_bytes(), mime=row.get('content_type', 'application/octet-stream'), cache='private, max-age=86400')
                else:
                    raise ReviewError('Not found.', 404)
            except ReviewError as exc:
                self.send({'error': str(exc)}, exc.status)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.send({'error': 'Could not read this record. Check the server terminal.'}, 500)

        def do_POST(self):
            try:
                self.host_check()
                origin = self.headers.get('Origin')
                if origin and origin not in {'http://' + self.headers.get('Host', '')}:
                    raise ReviewError('Cross-origin writes are not allowed.', 403)
                if not secrets.compare_digest(self.headers.get('X-Review-Token', ''), store.token):
                    raise ReviewError('Review token missing or expired. Reload the page.', 403)
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536 or self.headers.get_content_type() != 'application/json':
                    raise ReviewError('Send a JSON request smaller than 64 KB.')
                try:
                    payload = json.loads(self.rfile.read(length))
                except (ValueError, UnicodeDecodeError):
                    raise ReviewError('Invalid JSON.')
                if self.path == '/api/review':
                    self.send(store.update(payload))
                elif self.path == '/api/export':
                    self.send(store.export())
                else:
                    raise ReviewError('Not found.', 404)
            except ReviewError as exc:
                self.send({'error': str(exc)}, exc.status)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.send({'error': 'Could not save. Your request was not confirmed; reload the record before retrying.'}, 500)
    return Handler

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--data-root', type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    store = ReviewStore(args.data_root)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(store))
    print(f'SerpentShaper image review: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()

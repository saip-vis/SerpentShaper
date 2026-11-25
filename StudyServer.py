"""Serve the local SerpentShaper MVP and an in-memory study index."""
import argparse
import base64
import binascii
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from study_retrieval import MAX_FILE_BYTES, StudyIndex

ROOT=Path(__file__).resolve().parent
MAX_REQUEST_BYTES=(MAX_FILE_BYTES*4//3)+4096


def make_handler(index):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def valid_host(self):
            return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'

        def write_json(self, status, payload):
            body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

        def do_GET(self):
            if not self.valid_host(): return self.write_json(403,{'error':'Invalid host.'})
            route=urlsplit(self.path)
            if route.path=='/api/study-search':
                try:
                    q=parse_qs(route.query).get('q',[''])[0]
                    return self.write_json(200,{'results':index.search(q)})
                except ValueError as exc: return self.write_json(400,{'error':str(exc)})
            if route.path=='/':
                self.send_response(302);self.send_header('Location','/MainInterface/index.html');self.end_headers();return
            path=Path(route.path.lstrip('/'))
            if (not path.parts or path.parts[0] not in {'MainInterface','PhysicalRendererTest'}
                or path.suffix.lower() not in {'.html','.css','.js'}
                or '..' in path.parts):
                return self.write_json(404,{'error':'Not found.'})
            resolved=(ROOT/path).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.is_file():
                return self.write_json(404,{'error':'Not found.'})
            return super().do_GET()

        def do_POST(self):
            if not self.valid_host() or self.headers.get('Origin')!=f'http://127.0.0.1:{self.server.server_port}':
                return self.write_json(403,{'error':'Invalid request origin.'})
            if self.headers.get_content_type()!='application/json':
                return self.write_json(415,{'error':'JSON is required.'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<=0 or length>MAX_REQUEST_BYTES: raise ValueError('Invalid request size.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict): raise ValueError('Invalid request.')
                route=urlsplit(self.path).path
                if route=='/api/study-upload':
                    encoded=payload.get('content')
                    if not isinstance(encoded,str): raise ValueError('File content is required.')
                    content=base64.b64decode(encoded,validate=True)
                    return self.write_json(200,index.add(payload.get('name'),content))
                if route=='/api/study-clear':
                    index.clear();return self.write_json(200,{'cleared':True})
                if route=='/api/study-answer':
                    from study_answer import answer
                    return self.write_json(200,answer(index,payload.get('question')))
                return self.write_json(404,{'error':'Not found.'})
            except (ValueError,UnicodeDecodeError,binascii.Error) as exc:
                return self.write_json(400,{'error':str(exc) or 'Invalid request.'})

        def log_message(self, format, *args):
            # Do not log uploaded text or queries.
            pass
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8768)
    args=parser.parse_args()
    if not 1<=args.port<=65535: parser.error('Port must be between 1 and 65535.')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(StudyIndex()))
    print(f'SerpentShaper: http://127.0.0.1:{args.port}/',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__':main()

"""Local-only HTTP server, image recognition and durable personal scores."""
import argparse
import base64
import binascii
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
from urllib.parse import urlsplit
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parent
PREFERRED_PORTS = [8585, 8888, 8090, 9000, 5050]
MAX_BODY = 24 * 1024 * 1024
FORMATS = {'.musicxml', '.xml', '.mxl', '.gp', '.gp3', '.gp4', '.gp5', '.gpx'}
ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')
STORE_LOCK = threading.Lock()
for ext, kind in {'.js':'application/javascript', '.sf2':'application/octet-stream',
                  '.musicxml':'application/xml', '.mxl':'application/vnd.recordare.musicxml'}.items():
    mimetypes.add_type(kind, ext)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def score_directory(server):
    path = Path(getattr(server, 'data_dir', ROOT / 'data' / 'scores'))
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class StudioHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('directory', str(ROOT))
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def send_json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def same_origin(self):
        host = self.headers.get('Host', '')
        try:
            if urlsplit('http://' + host).hostname not in ('localhost', '127.0.0.1', '::1'):
                return False
        except ValueError:
            return False
        origin = self.headers.get('Origin')
        return not origin or origin == 'http://' + host

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise ValueError('Se esperaba una solicitud JSON.')
        length = int(self.headers.get('Content-Length', '0'))
        if length <= 0 or length > MAX_BODY:
            raise ValueError('La solicitud está vacía o supera el límite de 24 MB.')
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict): raise ValueError('La solicitud debe ser un objeto JSON.')
        return data

    def do_GET(self):
        if not self.same_origin(): return self.send_json({'error': 'Origen no permitido.'}, 403)
        path = urlsplit(self.path).path
        if path == '/api/health':
            return self.send_json({'success': True, 'application': 'DrumScore Studio', 'version': '1.1.0'})
        if path == '/api/scores':
            records = []
            for f in score_directory(self.server).glob('*.json'):
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    records.append({k: data[k] for k in ('id', 'title', 'filename', 'updatedAt')})
                except (ValueError, KeyError, OSError): continue
            return self.send_json({'scores': sorted(records, key=lambda x: x['updatedAt'], reverse=True)})
        if path.startswith('/api/scores/'):
            identifier = path.rsplit('/', 1)[-1]
            if not ID_PATTERN.fullmatch(identifier): return self.send_json({'error': 'Partitura no encontrada.'}, 404)
            f = score_directory(self.server) / f'{identifier}.json'
            try: return self.send_json(json.loads(f.read_text(encoding='utf-8')))
            except (FileNotFoundError, ValueError): return self.send_json({'error': 'Partitura no encontrada.'}, 404)
        # The user library is available through the API, never as a directory listing.
        if path not in ('/', '/index.html', '/favicon.ico') and not path.startswith(('/assets/', '/js/', '/css/')):
            return self.send_error(404)
        target = Path(self.translate_path(self.path)).resolve()
        allowed_roots = [ROOT / name for name in ('assets', 'js', 'css')]
        if path not in ('/', '/index.html', '/favicon.ico') and not any(target.is_relative_to(p) for p in allowed_roots):
            return self.send_error(404)
        return super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        if not self.same_origin():
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if 0 < length <= MAX_BODY: self.rfile.read(length)
            except Exception: pass
            return self.send_json({'success': False, 'error': 'Origen no permitido.'}, 403)
        try:
            data = self.read_json()
            path = urlsplit(self.path).path
            if path == '/api/parse-image':
                from drum_omr import DrumOMR
                raw = data.get('image', '')
                if not isinstance(raw, str): raise ValueError('La imagen no es válida.')
                raw = raw.split(',', 1)[-1]
                image = base64.b64decode(raw, validate=True)
                if not image or len(image) > 16 * 1024 * 1024: raise ValueError('La imagen debe pesar hasta 16 MB.')
                return self.send_json(DrumOMR().process_image(image, config=data.get('config')))
            if path == '/api/compile-grid':
                from score_grid import compile_grid
                return self.send_json(compile_grid(data.get('grid'), data.get('config')))
            if path == '/api/scores':
                identifier = data.get('id') or uuid.uuid4().hex
                if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier): raise ValueError('Identificador de partitura inválido.')
                filename = str(data.get('filename', 'partitura.musicxml'))[:180]
                if Path(filename).suffix.lower() not in FORMATS: raise ValueError('Formato de partitura no admitido.')
                encoded = data.get('data', '')
                content = base64.b64decode(encoded, validate=True)
                if not content or len(content) > 16 * 1024 * 1024: raise ValueError('El archivo está vacío o supera 16 MB.')
                grid, config = data.get('grid'), data.get('config')
                if grid is not None:
                    from score_grid import compile_grid
                    result = compile_grid(grid, config)
                    grid, config = result['grid'], result['config']
                    content = result['musicXml'].encode('utf-8')
                    encoded = base64.b64encode(content).decode('ascii')
                record = {'id': identifier, 'title': str(data.get('title') or filename)[:160],
                          'filename': filename, 'data': encoded, 'grid': grid, 'config': config,
                          'settings': data.get('settings', {}),
                          'updatedAt': datetime.now(timezone.utc).isoformat()}
                with STORE_LOCK: atomic_json(score_directory(self.server) / f'{identifier}.json', record)
                return self.send_json({'success': True, 'id': identifier})
            return self.send_json({'success': False, 'error': 'Ruta no encontrada.'}, 404)
        except ModuleNotFoundError:
            self.send_json({'success': False, 'error': 'Faltan las dependencias de reconocimiento. Ejecutá instalar_dependencias.bat.'}, 503)
        except (ValueError, TypeError, KeyError, binascii.Error) as e:
            self.send_json({'success': False, 'error': str(e)}, 400)
        except OSError:
            self.send_json({'success': False, 'error': 'No se pudo leer la imagen o guardar el archivo. Revisá el formato y los permisos de la carpeta.'}, 400)
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}', file=sys.stderr)
            self.send_json({'success': False, 'error': 'No se pudo completar la operación. Revisá la consola del servidor.'}, 500)

    def handle_one_request(self):
        try: super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError): pass

    def copyfile(self, source, outputfile):
        try: super().copyfile(source, outputfile)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError): pass


def run_server():
    parser = argparse.ArgumentParser(description='DrumScore Studio local')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int)
    args = parser.parse_args()
    ports = [args.port] if args.port is not None else PREFERRED_PORTS + [0]
    httpd = None
    for port in ports:
        try:
            httpd = ThreadingHTTPServer(('127.0.0.1', port), StudioHTTPRequestHandler)
            break
        except OSError: continue
    if httpd is None:
        raise SystemExit('No se pudo abrir el puerto solicitado. Probá otro puerto con --port.')
    url = f'http://localhost:{httpd.server_port}'
    print(f'DrumScore Studio\nAbrí {url}\nCtrl+C para detener el servidor.')
    if not args.no_browser:
        timer = threading.Timer(0.6, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    try: httpd.serve_forever()
    except KeyboardInterrupt: print('\nServidor detenido.')
    finally: httpd.server_close()


if __name__ == '__main__': run_server()

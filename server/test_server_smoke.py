"""Small local smoke test for the standard-library HTTP server (no third-party deps)."""
import importlib.util
import json
import tempfile
import threading
import urllib.request
from pathlib import Path

SERVER_FILE = Path(__file__).with_name('server.py')
spec = importlib.util.spec_from_file_location('pcshield_server', SERVER_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.clean_media_title('Dune.Part.Two.2024.2160p.WEB-DL.x265.mkv') == ('Dune Part Two', '2024')
assert mod.clean_media_title('Some Movie (2021).mkv') == ('Some Movie', '2021')
assert mod.clean_media_title('The.Last.of.Us.S01E01.1080p.mkv')[0] == 'The Last of Us'

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    payload = b'PCShieldStream range smoke test\n'
    (root / 'sample.mp4').write_bytes(payload)
    mod.ROOTS = [root]
    httpd = mod.ThreadingHTTPServer(('127.0.0.1', 0), mod.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{httpd.server_port}'
    try:
        with urllib.request.urlopen(base + '/api/health') as response:
            assert json.loads(response.read())['ok'] is True
        with urllib.request.urlopen(base + '/api/list?path=0%3A') as response:
            assert any(x['name'] == 'sample.mp4' for x in json.loads(response.read())['items'])
        request = urllib.request.Request(base + '/stream?path=0%3Asample.mp4', headers={'Range': 'bytes=0-5'})
        with urllib.request.urlopen(request) as response:
            assert response.status == 206
            assert response.headers['Content-Range'] == f'bytes 0-5/{len(payload)}'
            assert response.read() == payload[:6]
        request = urllib.request.Request(base + '/stream?path=0%3Asample.mp4', method='HEAD')
        with urllib.request.urlopen(request) as response:
            assert response.headers['Accept-Ranges'] == 'bytes'
            assert int(response.headers['Content-Length']) == len(payload)
        print('PASS: health, list, HTTP Range, HEAD')
    finally:
        httpd.shutdown()
        httpd.server_close()

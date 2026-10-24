"""Small local smoke test for the standard-library HTTP server (no third-party deps)."""
import importlib.util
import json
import tempfile
import threading
import urllib.error
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
    (root / 'sample.en.srt').write_text('1\n00:00:00,000 --> 00:00:01,000\nhello\n', encoding='utf-8')
    (root / 'sample Extended.srt').write_text('wrong match', encoding='utf-8')
    mod.ROOTS = [root]
    mod.DB_PATH = root / 'progress.json'
    mod.PROGRESS_DB = {}
    mod.POSTER_DB_PATH = root / 'posters.json'
    mod.POSTER_CACHE = {}
    httpd = mod.LANThreadingHTTPServer(('127.0.0.1', 0), mod.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{httpd.server_port}'
    try:
        with urllib.request.urlopen(base + '/api/health') as response:
            health = json.loads(response.read())
            assert health['ok'] is True and health['version'] == '1.3.0'
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
        with urllib.request.urlopen(base + '/api/subtitles?path=0%3Asample.mp4') as response:
            subs = json.loads(response.read())['items']
            assert [x['name'] for x in subs] == ['sample.en.srt']
        data = json.dumps({'path':'0:sample.mp4','positionMs':12345}).encode()
        request = urllib.request.Request(base + '/api/progress', data=data, headers={'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(request) as response:
            assert json.loads(response.read())['ok'] is True
        with urllib.request.urlopen(base + '/api/progress?path=0%3Asample.mp4') as response:
            assert json.loads(response.read())['positionMs'] == 12345
        assert json.loads((root / 'progress.json').read_text())['0:sample.mp4'] == 12345

        # A genuine no-result is negatively cached; transient network errors are not.
        poster_calls = {'no_result': 0, 'failure': 0}
        def fake_no_result(filename):
            poster_calls['no_result'] += 1
            return {'poster': None, 'title': Path(filename).stem, 'lookupFailed': False}
        mod.lookup_poster = fake_no_result
        for _ in range(2):
            with urllib.request.urlopen(base + '/api/poster?path=0%3Asample.mp4') as response:
                assert json.loads(response.read())['poster'] is None
        assert poster_calls['no_result'] == 1
        assert mod.POSTER_CACHE[mod.key_for(root / 'sample.mp4')]['_cachedAt'] > 0

        (root / 'temporary.mp4').write_bytes(payload)
        def fake_failure(filename):
            poster_calls['failure'] += 1
            return {'poster': None, 'title': Path(filename).stem, 'lookupFailed': True}
        mod.lookup_poster = fake_failure
        for _ in range(2):
            with urllib.request.urlopen(base + '/api/poster?path=0%3Atemporary.mp4') as response:
                assert json.loads(response.read())['lookupFailed'] is True
        assert poster_calls['failure'] == 2
        assert mod.key_for(root / 'temporary.mp4') not in mod.POSTER_CACHE
        assert httpd.verify_request(None, ('127.0.0.1', 1)) is True
        assert httpd.verify_request(None, ('8.8.8.8', 1)) is False
        print('PASS: health, list, HTTP Range, HEAD, subtitles, progress, poster cache, LAN client filter')
    finally:
        httpd.shutdown()
        httpd.server_close()

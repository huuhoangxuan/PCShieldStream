#!/usr/bin/env python3
"""PCShieldStream LAN media server. Python standard library only."""
import argparse, json, mimetypes, os, socket, threading, urllib.parse, urllib.request, re, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

VIDEO_EXTS={'.mkv','.mp4','.m4v','.mov','.avi','.webm','.ts','.m2ts','.mpg','.mpeg','.wmv','.flv','.ogv'}
SUB_EXTS={'.srt','.ass','.ssa','.vtt'}
ROOTS=[]
DB_PATH=Path(__file__).with_name('progress.json')
POSTER_DB_PATH=Path(__file__).with_name('posters.json')
LOCK=threading.Lock()
POSTER_LOCK=threading.Lock()
POSTER_CACHE={}

def load_db():
    try: return json.loads(DB_PATH.read_text('utf-8'))
    except Exception: return {}
def save_db(db):
    tmp=DB_PATH.with_suffix('.tmp'); tmp.write_text(json.dumps(db,ensure_ascii=False,indent=2),'utf-8'); tmp.replace(DB_PATH)
def key_for(p): return str(p).casefold()
def load_poster_cache():
    global POSTER_CACHE
    try: POSTER_CACHE=json.loads(POSTER_DB_PATH.read_text('utf-8'))
    except Exception: POSTER_CACHE={}
def save_poster_cache():
    try:
        tmp=POSTER_DB_PATH.with_suffix('.tmp'); tmp.write_text(json.dumps(POSTER_CACHE,ensure_ascii=False,indent=2),'utf-8'); tmp.replace(POSTER_DB_PATH)
    except Exception as e: print('[poster] cache save failed:',repr(e))
def clean_media_title(filename):
    stem=Path(filename).stem
    stem=re.sub(r'[._]+',' ',stem)
    stem=re.sub(r'\[[^\]]*\]|\([^)]*(?:1080p|2160p|720p|x264|x265|hevc|bluray|web.?dl|hdr|dv)[^)]*\)',' ',stem,flags=re.I)
    stem=re.sub(r'\b(2160p|1080p|720p|480p|4k|8k|x264|x265|h264|h265|hevc|av1|bluray|blu.?ray|web.?dl|webrip|brrip|hdr10\+?|dv|dovi|aac\d*|dts(?:-hd)?|truehd|proper|repack|remux)\b',' ',stem,flags=re.I)
    # Remove TV episode tokens so lookup searches for the series title.
    stem=re.sub(r'\bS\d{1,2}E\d{1,2}\b.*$', ' ', stem, flags=re.I)
    stem=re.sub(r'\bSeason\s*\d+\s*Episode\s*\d+\b.*$', ' ', stem, flags=re.I)
    stem=re.sub(r'\s+',' ',stem).strip(' -_')
    year_match=re.search(r'\b(19\d{2}|20\d{2})\b',stem)
    year=year_match.group(1) if year_match else None
    if year_match: stem=stem[:year_match.start()].strip(' -_(')
    stem=re.sub(r'[()\[\]]',' ',stem)
    stem=re.sub(r'\s+',' ',stem).strip(' -_')
    return stem or Path(filename).stem, year

def lookup_poster(filename):
    title, year=clean_media_title(filename)
    if not title: return {'poster':None,'title':Path(filename).stem}
    encoded_title=urllib.parse.quote(title, safe='')
    for kind in ('movie','series'):
        endpoint=f'https://v3-cinemeta.strem.io/catalog/{kind}/top/search={encoded_title}.json'
        try:
            req=urllib.request.Request(endpoint,headers={'User-Agent':'PCShieldStream/1.0','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=4) as response: payload=json.loads(response.read().decode('utf-8','replace'))
            metas=payload.get('metas',[])
            if not metas: continue
            norm=lambda x: re.sub(r'[^a-z0-9]','',str(x).lower())
            exact=[m for m in metas if norm(m.get('name',''))==norm(title)]
            choices=exact or metas
            if year:
                year_match=[m for m in choices if str(m.get('year',''))==year]
                if year_match: choices=year_match
            for meta in choices:
                poster=meta.get('poster') or meta.get('posterShape')
                if poster and str(poster).startswith('https://'):
                    return {'poster':poster,'title':meta.get('name') or title,'year':meta.get('year')}
        except Exception as e:
            print('[poster] lookup failed for',title,':',repr(e))
    return {'poster':None,'title':title}

def resolve_path(raw):
    # Client paths are root-index + relative path, never arbitrary absolute paths.
    raw=raw or ''
    idx, sep, rel=raw.partition(':')
    if not sep or not idx.isdigit() or int(idx)>=len(ROOTS): raise ValueError('Invalid root')
    root=ROOTS[int(idx)]
    candidate=(root / Path(rel.replace('\\','/'))).resolve()
    if candidate != root and root not in candidate.parents: raise ValueError('Path outside configured root')
    return candidate

def roots_json(): return [{'path':str(p),'name':p.name or str(p),'id':str(i)} for i,p in enumerate(ROOTS)]
def child_path(parent, name): return parent + name if parent.endswith(':') else parent.rstrip('/') + '/' + name
class Handler(BaseHTTPRequestHandler):
    server_version='PCShieldStream/1.2.0'
    def log_message(self, fmt, *args): print('[%s] %s' % (self.address_string(), fmt%args))
    def send_json(self, obj, status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(data)
    def do_HEAD(self):
        u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
        if u.path not in ('/stream','/subtitle'):
            return self.send_error(404)
        try:
            p=resolve_path(q.get('path',[''])[0])
            if not p.is_file(): return self.send_error(404)
            if u.path=='/stream' and p.suffix.lower() not in VIDEO_EXTS: return self.send_error(415)
            if u.path=='/subtitle' and p.suffix.lower() not in SUB_EXTS: return self.send_error(415)
            size=p.stat().st_size
            mime=mimetypes.guess_type(str(p))[0] or ('text/plain' if u.path=='/subtitle' else 'application/octet-stream')
            self.send_response(200); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(size)); self.send_header('Accept-Ranges','bytes'); self.end_headers()
        except (ValueError,PermissionError) as e: return self.send_json({'error':str(e)},400)
        except FileNotFoundError: return self.send_error(404)

    def do_GET(self):
        u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
        try:
            if u.path=='/api/health': return self.send_json({'ok':True,'name':'PCShieldStream','version':'1.2.0'})
            if u.path=='/api/roots': return self.send_json({'roots':roots_json()})
            if u.path=='/api/list':
                raw=q.get('path',[''])[0]
                if not raw: return self.send_json({'items':[{'name':r.name or str(r),'path':f'{i}:','type':'dir','root':True} for i,r in enumerate(ROOTS)]})
                p=resolve_path(raw)
                if not p.is_dir(): raise ValueError('Not a directory')
                items=[]
                for x in sorted(p.iterdir(),key=lambda x:(not x.is_dir(),x.name.casefold())):
                    try:
                        if x.is_dir(): items.append({'name':x.name,'path':child_path(raw, x.name),'type':'dir'})
                        elif x.is_file() and x.suffix.lower() in VIDEO_EXTS: items.append({'name':x.name,'path':child_path(raw, x.name),'type':'video','size':x.stat().st_size})
                    except (PermissionError,OSError): pass
                return self.send_json({'path':raw,'items':items})
            if u.path=='/api/subtitles':
                video=resolve_path(q.get('path',[''])[0]); subs=[]
                for x in video.parent.iterdir():
                    if x.is_file() and x.suffix.lower() in SUB_EXTS and x.stem.casefold().startswith(video.stem.casefold()):
                        subs.append({'name':x.name,'path':child_path(q.get('path',[''])[0].rsplit('/',1)[0] if '/' in q.get('path',[''])[0] else q.get('path',[''])[0].split(':',1)[0]+':', x.name)})
                return self.send_json({'items':subs})
            if u.path=='/api/poster':
                raw=q.get('path',[''])[0]
                p=resolve_path(raw)
                if not p.is_file() or p.suffix.lower() not in VIDEO_EXTS: return self.send_json({'poster':None,'title':p.stem})
                cache_key=key_for(p)
                with POSTER_LOCK:
                    cached=POSTER_CACHE.get(cache_key)
                    if cached is not None: return self.send_json(cached)
                result=lookup_poster(p.name)
                # Cache only successful lookups. A temporary network failure must not
                # permanently suppress poster lookup for this file.
                if result.get('poster'):
                    with POSTER_LOCK:
                        POSTER_CACHE[cache_key]=result
                        save_poster_cache()
                return self.send_json(result)
            if u.path=='/api/progress':
                p=q.get('path',[''])[0]
                with LOCK: value=load_db().get(p,0)
                return self.send_json({'positionMs':value})
            if u.path in ('/stream','/subtitle'):
                p=resolve_path(q.get('path',[''])[0])
                if not p.is_file(): return self.send_error(404)
                if u.path=='/stream' and p.suffix.lower() not in VIDEO_EXTS: return self.send_error(415)
                if u.path=='/subtitle' and p.suffix.lower() not in SUB_EXTS: return self.send_error(415)
                size=p.stat().st_size; start=0; end=size-1; status=200
                rng=self.headers.get('Range')
                if rng:
                    try:
                        unit, val=rng.split('=',1)
                        if unit.strip().lower()!='bytes' or ',' in val or size <= 0: raise ValueError()
                        a,b=val.strip().split('-',1)
                        if not a and not b: raise ValueError()
                        if not a:
                            suffix=int(b)
                            if suffix <= 0: raise ValueError()
                            start=max(0,size-suffix); end=size-1
                        else:
                            start=int(a); end=int(b) if b else size-1
                        if start < 0 or start >= size or end < start:
                            self.send_response(416); self.send_header('Content-Range',f'bytes */{size}'); self.send_header('Content-Length','0'); self.end_headers(); return
                        end=min(end,size-1); status=206
                    except Exception: return self.send_error(416)
                mime=mimetypes.guess_type(str(p))[0] or ('text/plain' if u.path=='/subtitle' else 'application/octet-stream')
                self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Accept-Ranges','bytes'); self.send_header('Content-Length',str(end-start+1)); self.send_header('Cache-Control','no-store')
                if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                self.end_headers()
                try:
                    with p.open('rb') as f:
                        f.seek(start); remaining=end-start+1
                        while remaining:
                            chunk=f.read(min(256*1024,remaining))
                            if not chunk: break
                            self.wfile.write(chunk); remaining-=len(chunk)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    # Players commonly cancel an HTTP request when probing formats,
                    # switching tracks, or closing playback. The client disconnect
                    # is not a server-side 500 error.
                    print('[stream] client closed connection before transfer completed:', p.name)
                return
            return self.send_error(404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # A TV player may cancel a request while probing a file or seeking.
            # The peer is already gone, so do not attempt to write an HTTP 500.
            print('[http] client disconnected during response')
        except (ValueError,PermissionError) as e: return self.send_json({'error':str(e)},400)
        except FileNotFoundError: return self.send_error(404)
        except Exception as e: print('ERROR',repr(e)); return self.send_error(500)
    def do_POST(self):
        if urllib.parse.urlparse(self.path).path!='/api/progress': return self.send_error(404)
        try:
            data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0')) or 0)); p=data['path']; pos=max(0,int(data['positionMs']))
            # Validate path against configured roots before saving state.
            resolve_path(p)
            with LOCK:
                db=load_db(); db[p]=pos; save_db(db)
            return self.send_json({'ok':True})
        except Exception as e: return self.send_json({'error':str(e)},400)

def local_ips():
    out=[]
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('192.0.2.1',80)); out.append(s.getsockname()[0]); s.close()
    except Exception: pass
    out.append('127.0.0.1'); return list(dict.fromkeys(out))

def main():
    global ROOTS
    ap=argparse.ArgumentParser(description='Stream local video files to NVIDIA Shield over your home LAN')
    ap.add_argument('--root',action='append',required=True,help='Allowed movie folder; repeat for multiple folders')
    ap.add_argument('--port',type=int,default=8787)
    args=ap.parse_args(); ROOTS=[]
    load_poster_cache()
    for item in args.root:
        p=Path(item).expanduser().resolve()
        if not p.is_dir(): ap.error(f'Folder does not exist: {p}')
        ROOTS.append(p)
    httpd=ThreadingHTTPServer(('0.0.0.0',args.port),Handler)
    print('\nPCShieldStream server running. Open one of these on Shield:')
    for ip in local_ips(): print(f'  http://{ip}:{args.port}')
    print('Allowed folders:'); [print('  -',p) for p in ROOTS]
    print('Poster lookup: Cinemeta metadata (cached locally in posters.json)')
    print('Keep this window open while watching. Ctrl+C to stop.\n')
    try: httpd.serve_forever()
    except KeyboardInterrupt: print('\nStopping server...')
    finally: httpd.server_close()
if __name__=='__main__': main()

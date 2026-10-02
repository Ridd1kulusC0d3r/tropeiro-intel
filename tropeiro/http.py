"""HTTP simples (stdlib) com retry seletivo, limite por host e cache opcional."""
import json, urllib.request, urllib.error, urllib.parse, time, random, threading
from pathlib import Path
from .storage.cache import FileCache

UA={'User-Agent':'TropeiroIntel/4.5 defensive-osint'}
RETRY_STATUS={429,500,502,503,504}
MIN_INTERVAL=1.0  # segundos entre chamadas ao mesmo host
_last_call={}
_lock=threading.Lock()
_cache=None

def set_cache(path=None,ttl=3600):
    """Ativa cache em disco para GETs. `set_cache(None)` desativa."""
    global _cache
    _cache=FileCache(Path(path).expanduser(),ttl) if path else None

def _throttle(url):
    host=urllib.parse.urlsplit(url).hostname or ''
    with _lock:
        wait=_last_call.get(host,0)+MIN_INTERVAL-time.monotonic()
        _last_call[host]=time.monotonic()+max(wait,0)
    if wait>0: time.sleep(wait)

def _retry_after(err,default):
    try: return min(float(err.headers.get('Retry-After')),30.0)
    except (TypeError,ValueError,AttributeError): return default

def request(url,headers=None,timeout=30,as_json=True,method='GET',payload=None,retries=2,backoff=.8):
    body=None
    h={**UA,**(headers or {})}
    if payload is not None:
        body=json.dumps(payload).encode();h.setdefault('Content-Type','application/json')
    key=f'{method} {url} {as_json}'
    if _cache is not None and method=='GET' and not headers:
        hit=_cache.get(key)
        if hit is not None: return hit
    last=None
    for attempt in range(max(1,int(retries)+1)):
        _throttle(url)
        try:
            req=urllib.request.Request(url,data=body,headers=h,method=method)
            with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read().decode('utf-8','replace')
            out=json.loads(data) if as_json else data
            if _cache is not None and method=='GET' and not headers: _cache.set(key,out)
            return out
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in RETRY_STATUS or attempt>=retries: raise
            time.sleep(_retry_after(e,backoff*(2**attempt))+random.random()*.15)
        except (urllib.error.URLError,TimeoutError,ConnectionError) as e:
            last=e
            if attempt>=retries: raise
            time.sleep(backoff*(2**attempt)+random.random()*.15)
    raise last

def get(url,headers=None,timeout=30,as_json=True,retries=2):return request(url,headers,timeout,as_json,'GET',None,retries)
def post_json(url,payload,headers=None,timeout=30,retries=2):return request(url,headers,timeout,True,'POST',payload,retries)

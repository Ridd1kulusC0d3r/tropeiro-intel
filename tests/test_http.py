import io, urllib.error
import pytest
from tropeiro import http
from tropeiro.utils import valid_hostname

class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*a): return False

def _err(code):
    return urllib.error.HTTPError('http://x',code,'e',{},io.BytesIO(b''))

@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(http,'MIN_INTERVAL',0)
    monkeypatch.setattr(http.time,'sleep',lambda s:None)
    http.set_cache(None)

def test_no_retry_on_404(monkeypatch):
    calls=[]
    def fake(req,timeout=0): calls.append(1); raise _err(404)
    monkeypatch.setattr(http.urllib.request,'urlopen',fake)
    with pytest.raises(urllib.error.HTTPError): http.get('http://x.test/a')
    assert len(calls)==1

def test_retry_on_429_then_ok(monkeypatch):
    seq=[_err(429),_Resp(b'{"ok":1}')]
    def fake(req,timeout=0):
        r=seq.pop(0)
        if isinstance(r,Exception): raise r
        return r
    monkeypatch.setattr(http.urllib.request,'urlopen',fake)
    assert http.get('http://x.test/b')=={'ok':1}

def test_cache_avoids_second_call(monkeypatch,tmp_path):
    calls=[]
    def fake(req,timeout=0): calls.append(1); return _Resp(b'{"v":2}')
    monkeypatch.setattr(http.urllib.request,'urlopen',fake)
    http.set_cache(tmp_path,60)
    assert http.get('http://x.test/c')==http.get('http://x.test/c')=={'v':2}
    assert len(calls)==1

def test_valid_hostname():
    assert valid_hostname('Example.COM.')=='example.com'
    assert valid_hostname('bücher.de')=='xn--bcher-kva.de'
    for bad in ['a.com/../x','a.com?x=1','a b.com','a.com&output=csv','','localhost']:
        assert valid_hostname(bad) is None

def test_crtsh_retries_once_on_transient_404(monkeypatch):
    from tropeiro.collectors import crtsh
    seq=[_err(404),_Resp(b'[{"name_value":"a.example"}]')]
    def fake(req,timeout=0):
        r=seq.pop(0)
        if isinstance(r,Exception): raise r
        return r
    monkeypatch.setattr(http.urllib.request,'urlopen',fake); monkeypatch.setattr(crtsh.time,'sleep',lambda s:None)
    assert crtsh.lookup('exemplo-fake.com')==[{'name_value':'a.example'}]

def test_crtsh_gives_up_after_the_second_failure_and_never_retries_400(monkeypatch):
    from tropeiro.collectors import crtsh
    calls=[]
    def fake(req,timeout=0): calls.append(1); raise _err(502)
    monkeypatch.setattr(http.urllib.request,'urlopen',fake); monkeypatch.setattr(crtsh.time,'sleep',lambda s:None)
    with pytest.raises(urllib.error.HTTPError): crtsh.lookup('exemplo-fake.com')
    assert len(calls)==2
    calls.clear()
    def bad(req,timeout=0): calls.append(1); raise _err(400)
    monkeypatch.setattr(http.urllib.request,'urlopen',bad)
    with pytest.raises(urllib.error.HTTPError): crtsh.lookup('exemplo-fake.com')
    assert len(calls)==1

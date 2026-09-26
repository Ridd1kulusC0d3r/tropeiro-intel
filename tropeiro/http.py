import json, urllib.request, urllib.parse, time
UA={"User-Agent":"TropeiroIntel/1.0 defensive-osint"}

def get(url,headers=None,timeout=30,as_json=True):
    req=urllib.request.Request(url,headers={**UA,**(headers or {})})
    with urllib.request.urlopen(req,timeout=timeout) as r:body=r.read().decode('utf-8','replace')
    return json.loads(body) if as_json else body

def post_json(url,payload,headers=None,timeout=30):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={**UA,'Content-Type':'application/json',**(headers or {})},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8','replace'))

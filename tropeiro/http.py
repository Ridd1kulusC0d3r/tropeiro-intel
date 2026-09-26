import json, urllib.request, urllib.error, time, random
UA={'User-Agent':'TropeiroIntel/4.0 defensive-osint'}

def request(url,headers=None,timeout=30,as_json=True,method='GET',payload=None,retries=2,backoff=.8):
    body=None
    h={**UA,**(headers or {})}
    if payload is not None:
        body=json.dumps(payload).encode();h.setdefault('Content-Type','application/json')
    last=None
    for attempt in range(max(1,int(retries)+1)):
        try:
            req=urllib.request.Request(url,data=body,headers=h,method=method)
            with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read().decode('utf-8','replace')
            return json.loads(data) if as_json else data
        except Exception as e:
            last=e
            if attempt>=retries:raise
            time.sleep(backoff*(2**attempt)+random.random()*.15)
    raise last

def get(url,headers=None,timeout=30,as_json=True,retries=2):return request(url,headers,timeout,as_json,'GET',None,retries)
def post_json(url,payload,headers=None,timeout=30,retries=2):return request(url,headers,timeout,True,'POST',payload,retries)

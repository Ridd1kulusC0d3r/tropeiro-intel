import base64, urllib.parse
from ..http import get

BASE="https://fofa.info/api/v1/search/all"
DEFAULT_FIELDS=["host","ip","port","protocol","domain","asn","org","server","title","jarm","cert.issuer.org","cert.subject.org","cname_domain","link"]

def search(query, api_key, fields=None, size=100, page=1, full=False):
    if not api_key: raise ValueError("FOFA API key is required")
    fields=fields or DEFAULT_FIELDS
    q64=base64.b64encode(query.encode()).decode()
    params=urllib.parse.urlencode({"key":api_key,"qbase64":q64,"fields":",".join(fields),"size":min(int(size),10000),"page":int(page),"full":"true" if full else "false","r_type":"json"})
    data=get(f"{BASE}?{params}",timeout=60)
    if data.get("error"): raise RuntimeError(data.get("errmsg") or "FOFA API error")
    rows=[dict(zip(fields,values)) for values in data.get("results",[]) or []]
    return {"query":query,"size":data.get("size",0),"page":data.get("page",page),"rows":rows}

def search_domain(domain, api_key, size=100, full=False):
    return search(f'domain="{domain}"',api_key,size=size,full=full)

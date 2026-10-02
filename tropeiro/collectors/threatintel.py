import urllib.parse
from ..http import get, post_json
from ..utils import valid_hostname

def _host(domain):
    h=valid_hostname(domain)
    if not h: raise ValueError(f'hostname inválido: {domain!r}')
    return h

def otx_domain(domain): return get(f'https://otx.alienvault.com/api/v1/indicators/domain/{_host(domain)}/url_list?limit=500')
def virustotal_domain(domain,key): return get(f'https://www.virustotal.com/api/v3/domains/{_host(domain)}',headers={'x-apikey':key}) if key else {}
def threatfox_search(ioc,key): return post_json('https://threatfox-api.abuse.ch/api/v1/',{'query':'search_ioc','search_term':ioc,'exact_match':True},headers={'Auth-Key':key}) if key else {}
def urlhaus_lookup(url): return post_json('https://urlhaus-api.abuse.ch/v1/url/',{'url':url})
def phishtank_check(url,app_key=''):
    import urllib.request
    data=urllib.parse.urlencode({'url':url,'format':'json',**({'app_key':app_key} if app_key else {})}).encode()
    req=urllib.request.Request('https://checkurl.phishtank.com/checkurl/',data=data,headers={'User-Agent':'TropeiroIntel/1.0 defensive-osint'})
    with urllib.request.urlopen(req,timeout=30) as r:
        import json; return json.loads(r.read().decode('utf-8','replace'))

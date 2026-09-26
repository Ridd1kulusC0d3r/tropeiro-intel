import urllib.parse
from ..http import get

def search(domain,api_key=''):
    q=urllib.parse.urlencode({'q':f'domain:{domain}','size':100}); h={'api-key':api_key} if api_key else {}
    return get('https://urlscan.io/api/v1/search/?'+q,headers=h)

def result(scan_id,api_key=''):
    h={'api-key':api_key} if api_key else {}
    return get(f'https://urlscan.io/api/v1/result/{scan_id}/',headers=h,timeout=60)

def redirects(scan_result):
    return scan_result.get('data',{}).get('redirects',[]) if isinstance(scan_result,dict) else []

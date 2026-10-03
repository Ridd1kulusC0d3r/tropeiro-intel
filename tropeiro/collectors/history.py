import urllib.parse, json
from ..http import get
from ..utils import valid_hostname

def wayback(domain,limit=3000):
    domain=valid_hostname(domain)
    if not domain: raise ValueError('hostname inválido')
    q=urllib.parse.urlencode({'url':f'*.{domain}/*','output':'json','fl':'original,timestamp,statuscode','collapse':'urlkey','limit':limit})
    d=get('https://web.archive.org/cdx/search/cdx?'+q,timeout=20,retries=0)   # fonte lenta/instável: 1 tentativa, o prazo da busca decide
    return d[1:] if isinstance(d,list) and d else []

def commoncrawl(domain,limit=1000):
    domain=valid_hostname(domain)
    if not domain: raise ValueError('hostname inválido')
    idx=get('https://index.commoncrawl.org/collinfo.json',retries=1)[0]['cdx-api']
    txt=get(f'{idx}?url=*.{domain}&output=json&limit={limit}',as_json=False,timeout=20,retries=0)
    return [json.loads(x) for x in txt.splitlines() if x.strip()]

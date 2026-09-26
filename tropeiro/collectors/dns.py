import urllib.parse
from ..http import get

def query(name,rtype='A'):
    q=urllib.parse.urlencode({'name':name,'type':rtype})
    d=get(f'https://cloudflare-dns.com/dns-query?{q}',{'accept':'application/dns-json'})
    return [x.get('data','') for x in d.get('Answer',[]) if x.get('data')]

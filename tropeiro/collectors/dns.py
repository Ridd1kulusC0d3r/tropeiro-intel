import urllib.parse
from ..http import get

def query(name,rtype='A'):
    q=urllib.parse.urlencode({'name':name,'type':rtype})
    d=get(f'https://cloudflare-dns.com/dns-query?{q}',{'accept':'application/dns-json'})
    return [x.get('data','') for x in d.get('Answer',[]) if x.get('data')]

def reverse_ptr(ip):
    """Nomes PTR (DNS reverso) de um IP, via DNS-over-HTTPS."""
    import ipaddress
    name=ipaddress.ip_address(ip).reverse_pointer
    return [x.rstrip('.') for x in query(name,'PTR')]

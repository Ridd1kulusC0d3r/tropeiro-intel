import re, ipaddress, urllib.parse
try:
    import tldextract
except Exception:
    tldextract=None
from collections import defaultdict
RE_URL=re.compile(r'https?://[^\s<>"\']+',re.I)
RE_EMAIL=re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I)
RE_IP=re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
RE_PHONE=re.compile(r'(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}(?!\d)')
RE_HASH=re.compile(r'\b(?:[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64})\b',re.I)
RE_DOMAIN=re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\b',re.I)

def hostname(value):
    v=value.strip()
    if '://' in v: return (urllib.parse.urlsplit(v).hostname or '').lower()
    return v.split('/')[0].split(':')[0].strip('.').lower()

def root_domain(value):
    h=hostname(value)
    if tldextract is not None:
        e=tldextract.extract(h)
        return '.'.join(x for x in [e.domain,e.suffix] if x)
    parts=[x for x in h.split('.') if x]
    if len(parts) <= 2: return h
    common_second={'com','net','org','gov','edu','co'}
    if len(parts)>=3 and len(parts[-1])==2 and parts[-2] in common_second:
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:])

def defang(v): return str(v).replace('https://','hxxps://').replace('http://','hxxp://').replace('.','[.]')

def extract_iocs(text):
    out=defaultdict(set); text=text or ''
    for x in RE_URL.findall(text): out['url'].add(x.rstrip('.,);]'))
    for x in RE_EMAIL.findall(text): out['email'].add(x.lower())
    for x in RE_IP.findall(text):
        try: ipaddress.ip_address(x); out['ip'].add(x)
        except ValueError: pass
    for x in RE_PHONE.findall(text):
        d=re.sub(r'\D','',x)
        if 10 <= len(d) <= 13: out['phone'].add(d)
    for x in RE_HASH.findall(text): out['hash'].add(x.lower())
    for x in RE_DOMAIN.findall(text): out['domain'].add(x.lower().strip('.'))
    for u in list(out['url']):
        h=hostname(u)
        if h: out['domain'].add(h)
    return {k:sorted(v) for k,v in out.items()}

RE_HOSTNAME=re.compile(r'^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$')

def valid_hostname(value):
    """Hostname seguro para entrar em URL de coletor (sem '/', '?', '&', espaços)."""
    h=(value or '').strip().lower().rstrip('.')
    try: h=h.encode('idna').decode('ascii')
    except UnicodeError: return None
    return h if RE_HOSTNAME.match(h) else None

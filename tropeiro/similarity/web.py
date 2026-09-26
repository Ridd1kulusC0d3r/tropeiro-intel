import hashlib, json, re
from urllib.parse import urlsplit

TRACKER_PATTERNS = {
    'google_analytics': re.compile(r'\bUA-\d{4,}-\d+\b|\bG-[A-Z0-9]{6,}\b',re.I),
    'google_tag_manager': re.compile(r'\bGTM-[A-Z0-9]{4,}\b',re.I),
    'google_adsense': re.compile(r'\bca-pub-\d{6,}\b',re.I),
    'facebook_pixel': re.compile(r'\b(?:fbq\s*\([^\n]{0,80}?|pixel[_-]?id["\'\s:=]+)(\d{6,20})',re.I),
    'statcounter': re.compile(r'\bsc_project\s*=\s*["\']?(\d{3,})',re.I),
}


def _canon_text(v):
    s=str(v or '')
    s=re.sub(r'\s+',' ',s)
    s=re.sub(r'(?i)(nonce|timestamp|token|session)["\'\s:=_-]+[A-Za-z0-9._-]{6,}',r'\1=<VAR>',s)
    return s.strip()


def sha256_text(v):return hashlib.sha256(_canon_text(v).encode('utf-8','ignore')).hexdigest()


def _walk(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from _walk(v,f'{path}.{k}' if path else str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):yield from _walk(v,f'{path}[{i}]')
    else:yield path,obj


def extract_durable_identifiers(scan_result):
    ids=[]; redirects=[]; resources=[]; titles=[]; strings=[]
    for path,val in _walk(scan_result or {}):
        if val is None:continue
        s=str(val); low=path.lower()
        strings.append(s)
        if 'redirect' in low and s.startswith(('http://','https://')):redirects.append(s)
        if any(x in low for x in ('url','request','href','src')) and s.startswith(('http://','https://')):
            resources.append(s)
        if low.endswith('title') and len(s)<300:titles.append(s)
    corpus='\n'.join(strings)
    for typ,rx in TRACKER_PATTERNS.items():
        for m in rx.finditer(corpus):
            val=m.group(1) if m.groups() and m.group(1) else m.group(0)
            ids.append({'type':typ,'value':val})
    uniq={(x['type'],x['value']):x for x in ids}
    return {
        'identifiers':sorted(uniq.values(),key=lambda x:(x['type'],x['value'])),
        'redirects':sorted(set(redirects)),
        'resource_hosts':sorted({urlsplit(x).hostname for x in resources if urlsplit(x).hostname}),
        'titles':sorted(set(titles)),
    }


def passive_web_fingerprint(scan_result):
    ex=extract_durable_identifiers(scan_result)
    data=scan_result or {}
    page=data.get('page',{}) if isinstance(data,dict) else {}
    task=data.get('task',{}) if isinstance(data,dict) else {}
    lists=data.get('lists',{}) if isinstance(data,dict) else {}
    features={
        'page_title':page.get('title'),
        'server':page.get('server'),
        'mime_type':page.get('mimeType'),
        'resource_hosts':ex['resource_hosts'],
        'redirect_hosts':sorted({urlsplit(x).hostname for x in ex['redirects'] if urlsplit(x).hostname}),
        'identifiers':ex['identifiers'],
        'ips':sorted(set(lists.get('ips',[]) or [])),
        'domains':sorted(set(lists.get('domains',[]) or [])),
    }
    raw=json.dumps(features,sort_keys=True,ensure_ascii=False,default=str)
    features['sha256']=hashlib.sha256(raw.encode()).hexdigest()
    return features

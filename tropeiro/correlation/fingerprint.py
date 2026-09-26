import hashlib, json, re
from urllib.parse import urlsplit
from collections import Counter

def fingerprint(cluster):
    urls=cluster.get('urls',[]); toks=[]
    for u in urls:
        try: toks += [x for x in re.split(r'[/_.-]+',urlsplit(u).path.lower()) if len(x)>=3]
        except Exception: pass
    pieces={'domains':sorted(cluster.get('domains',[])),'ips':sorted(cluster.get('ips',[])),'phones':sorted(cluster.get('phones',[])),'certificates':sorted(cluster.get('certificates',[])),'path_tokens':Counter(toks).most_common(20)}
    pieces['sha256']=hashlib.sha256(json.dumps(pieces,sort_keys=True).encode()).hexdigest(); return pieces

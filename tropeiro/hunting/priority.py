from datetime import datetime, timezone
try:
    from rapidfuzz.fuzz import ratio
except Exception:
    from difflib import SequenceMatcher
    def ratio(a,b): return 100*SequenceMatcher(None,a,b).ratio()
try:
    import tldextract
except Exception:
    tldextract=None

def days_since(iso):
    if not iso: return None
    try: return (datetime.now(timezone.utc)-datetime.fromisoformat(iso.replace('Z','+00:00')).astimezone(timezone.utc)).days
    except Exception: return None

def brand_similarity(domain,brand):
    if not brand: return 0
    label = tldextract.extract(domain).domain.lower() if tldextract is not None else domain.lower().split('.')[0]
    return ratio(label,(brand or '').lower())

def prioritize(domain,brand='',created=None,has_mx=False,existing_score=0):
    sim=brand_similarity(domain,brand); age=days_since(created); p=0; reasons=[]
    if sim>=85: p+=30; reasons.append(f'brand_similarity={sim:.0f}')
    elif sim>=65: p+=15; reasons.append(f'brand_similarity={sim:.0f}')
    if age is not None and age<=30: p+=25; reasons.append(f'domain_age={age}d')
    elif age is not None and age<=90: p+=12; reasons.append(f'domain_age={age}d')
    if has_mx: p+=8; reasons.append('mx_present')
    if existing_score>=40: p+=15; reasons.append('existing_case_signals')
    return min(100,p),reasons

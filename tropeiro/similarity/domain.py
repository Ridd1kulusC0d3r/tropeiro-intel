import re, unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from urllib.parse import urlsplit

try:
    from rapidfuzz.distance import Levenshtein, JaroWinkler
    _HAS_RF = True
except Exception:
    _HAS_RF = False

try:
    import tldextract
except Exception:
    tldextract = None

_CONFUSABLE = str.maketrans({
    '0':'o','1':'l','3':'e','4':'a','5':'s','7':'t','@':'a','$':'s'
})


def _host(v):
    s=str(v or '').strip().lower()
    if '://' in s:
        s=urlsplit(s).hostname or s
    return s.strip('.')


def split_domain(v):
    h=_host(v)
    if tldextract is not None:
        e=tldextract.extract(h)
        return e.subdomain, e.domain, e.suffix
    p=h.split('.')
    if len(p)>=2:
        return '.'.join(p[:-2]), p[-2], p[-1]
    return '', h, ''


def fold_label(s):
    s=unicodedata.normalize('NFKD',str(s or ''))
    s=''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+','',s.translate(_CONFUSABLE))


def _ngrams(s,n=3):
    s=f'^{s}$'
    if len(s)<n:return {s}
    return {s[i:i+n] for i in range(len(s)-n+1)}


def ngram_jaccard(a,b,n=3):
    A,B=_ngrams(a,n),_ngrams(b,n)
    return len(A&B)/max(1,len(A|B))


def token_set(v):
    sub,label,tld=split_domain(v)
    raw='-'.join(x for x in [sub,label] if x)
    return {x for x in re.split(r'[^a-z0-9]+',raw.lower()) if x}


def token_similarity(a,b):
    A,B=token_set(a),token_set(b)
    if not A or not B:return 0.0
    return len(A&B)/max(1,len(A|B))


def _edit_similarity(a,b):
    if not a and not b:return 1.0
    if not a or not b:return 0.0
    if _HAS_RF:
        return Levenshtein.normalized_similarity(a,b)
    from difflib import SequenceMatcher
    return SequenceMatcher(None,a,b).ratio()


def _jaro(a,b):
    if not a and not b:return 1.0
    if not a or not b:return 0.0
    if _HAS_RF:return JaroWinkler.normalized_similarity(a,b)
    from difflib import SequenceMatcher
    return SequenceMatcher(None,a,b).ratio()


def domain_similarity(a,b):
    _,la,ta=split_domain(a); _,lb,tb=split_domain(b)
    fa,fb=fold_label(la),fold_label(lb)
    lev=_edit_similarity(fa,fb)
    jaro=_jaro(fa,fb)
    ng=ngram_jaccard(fa,fb)
    tok=token_similarity(a,b)
    tld_same=1.0 if ta and tb and ta==tb else 0.0
    homoglyph=(fa==fb and la.lower()!=lb.lower())
    score=.34*lev+.26*jaro+.22*ng+.12*tok+.06*tld_same
    reasons=[]
    if lev>=.85:reasons.append('high_lexical_similarity')
    if jaro>=.90:reasons.append('high_jaro_winkler')
    if tok>=.5:reasons.append('token_overlap')
    if homoglyph:reasons.append('homoglyph_or_confusable_pattern')
    if ta!=tb and fa==fb:reasons.append('tld_swap')
    return {
        'left':_host(a),'right':_host(b),'score':round(min(1.0,score),4),
        'levenshtein':round(lev,4),'jaro_winkler':round(jaro,4),
        'ngram_jaccard':round(ng,4),'token_similarity':round(tok,4),
        'same_tld':bool(tld_same),'reasons':reasons,
    }


def candidate_pairs(domains,max_pairs=5000):
    """Avoid unbounded O(n²): small sets are exhaustive, large sets are bucketed by label shape."""
    vals=sorted({_host(x) for x in domains if _host(x)})
    if len(vals)<=120:
        return list(combinations(vals,2))[:max_pairs]
    buckets=defaultdict(list)
    for d in vals:
        _,label,_=split_domain(d); f=fold_label(label)
        key=(f[:2],len(f)//3)
        buckets[key].append(d)
        if len(f)>=4:buckets[(f[:1],len(f)//3)].append(d)
    seen=set(); out=[]
    for items in buckets.values():
        items=sorted(set(items))
        for pair in combinations(items,2):
            if pair in seen:continue
            seen.add(pair);out.append(pair)
            if len(out)>=max_pairs:return out
    return out


def compare_domains(domains,min_score=.45,max_pairs=5000):
    rows=[]
    for a,b in candidate_pairs(domains,max_pairs=max_pairs):
        r=domain_similarity(a,b)
        if r['score']>=min_score:rows.append(r)
    return sorted(rows,key=lambda x:x['score'],reverse=True)

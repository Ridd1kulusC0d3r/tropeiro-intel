import hashlib, re, unicodedata
try:
    from rapidfuzz.fuzz import token_set_ratio
except Exception:
    from difflib import SequenceMatcher
    def token_set_ratio(a,b):
        sa=" ".join(sorted(set(a.split())))
        sb=" ".join(sorted(set(b.split())))
        return 100*SequenceMatcher(None,sa,sb).ratio()

LEGAL_SUFFIXES = {"ltda","limitada","sa","s a","s/a","inc","llc","ltd","corp","corporation","company","co","gmbh","plc","eireli","me","mei"}

def fold(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()

def canonical_org(name):
    s = re.sub(r"[^\w\s-]", " ", fold(name))
    toks = [t for t in re.split(r"[\s_-]+", s) if t and t not in LEGAL_SUFFIXES]
    return " ".join(toks)

def org_similarity(a, b):
    ca, cb = canonical_org(a), canonical_org(b)
    if not ca or not cb: return 0.0
    return token_set_ratio(ca, cb) / 100.0

def protected_identifier(value, prefix="id"):
    h = hashlib.sha256(str(value).strip().lower().encode()).hexdigest()[:16]
    return f"{prefix}:{h}"

def resolve_orgs(names, threshold=0.90):
    clusters = []
    for name in [x for x in names if x]:
        placed = False
        for c in clusters:
            if max(org_similarity(name, x) for x in c) >= threshold:
                c.append(name); placed = True; break
        if not placed: clusters.append([name])
    return clusters

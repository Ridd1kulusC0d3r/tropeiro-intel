from urllib.parse import quote
from ..http import get

BASE="https://api.dnsdumpster.com"

def domain_lookup(domain, api_key, page=1, include_map=False):
    if not api_key: raise ValueError("DNSDumpster API key is required")
    suffix=f"?page={int(page)}"
    if include_map: suffix += "&map=1"
    return get(f"{BASE}/domain/{quote(domain)}{suffix}",headers={"X-API-Key":api_key},timeout=45)

def normalize(domain, payload):
    out={"domain":domain,"records":[],"asn_owners":set(),"netblocks":set()}
    for rtype in ("a","aaaa","mx","ns","cname"):
        for row in payload.get(rtype,[]) or []:
            rec={"type":rtype.upper(),"host":row.get("host") or row.get("name"),"ip":row.get("ip"),"asn":row.get("asn"),"asn_name":row.get("asn_name") or row.get("provider") or row.get("organization"),"netblock":row.get("netblock")}
            out["records"].append(rec)
            if rec["asn_name"]: out["asn_owners"].add(rec["asn_name"])
            if rec["netblock"]: out["netblocks"].add(rec["netblock"])
    out["asn_owners"]=sorted(out["asn_owners"]);out["netblocks"]=sorted(out["netblocks"])
    return out

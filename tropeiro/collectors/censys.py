from urllib.parse import quote
from ..http import get, post_json

BASE="https://api.platform.censys.io/v3"

def _headers(pat, organization_id=None):
    if not pat: raise ValueError("Censys Personal Access Token is required")
    h={"Authorization":f"Bearer {pat}"}
    if organization_id: h["X-Organization-ID"]=organization_id
    return h

def global_search(query, pat, organization_id=None, fields=None, page_size=50, page_token=None):
    payload={"query":query,"page_size":min(int(page_size),100)}
    if fields: payload["fields"]=fields
    if page_token: payload["page_token"]=page_token
    return post_json(f"{BASE}/global/search/query",payload,headers=_headers(pat,organization_id),timeout=60)

def search_domain(domain, pat, organization_id=None, page_size=50):
    return global_search(f'"{domain}"',pat,organization_id,fields=["host.ip","host.dns.names","host.autonomous_system.asn","host.autonomous_system.name","cert.fingerprint_sha256","cert.names","cert.parsed.subject_dn","cert.parsed.issuer_dn","web.hostname","web.port"],page_size=page_size)

def host_lookup(ip, pat, organization_id=None):
    return get(f"{BASE}/global/asset/host/{quote(ip)}",headers=_headers(pat,organization_id),timeout=45)

def certificate_lookup(sha256, pat, organization_id=None):
    return get(f"{BASE}/global/asset/certificate/{quote(sha256)}",headers=_headers(pat,organization_id),timeout=45)

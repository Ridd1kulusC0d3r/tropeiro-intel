"""Enriquecimentos do Workbench: respostas de fontes -> Observations (puro, testável sem rede)."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from ..models import Observation
from ..similarity.web import extract_durable_identifiers

def _obs(domain,source,value,notes=""):
    return Observation(str(domain),"domain",source,str(value),notes=notes)

def _cdx_time(ts):
    """20260920103000 -> 2026-09-20T10:30:00+00:00"""
    try: return datetime.strptime(str(ts)[:14],"%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).isoformat()
    except ValueError: return None

def wayback_obs(domain: str, rows: Iterable[Any], limit: int=50) -> List[Observation]:
    rows=[r for r in rows or [] if isinstance(r,(list,tuple)) and len(r)>=2]
    if not rows: return []
    stamps=sorted(t for t in (_cdx_time(r[1]) for r in rows) if t)
    out=[_obs(domain,"wayback:count",len(rows))]
    if stamps: out+=[_obs(domain,"wayback:first_seen",stamps[0]),_obs(domain,"wayback:last_seen",stamps[-1])]
    seen=set()
    for r in rows:
        if r[0] not in seen and len(seen)<limit: seen.add(r[0]); out.append(_obs(domain,"wayback",r[0]))
    return out

def commoncrawl_obs(domain: str, rows: Iterable[Any], limit: int=50) -> List[Observation]:
    urls=[r.get("url") for r in rows or [] if isinstance(r,dict) and r.get("url")]
    if not urls: return []
    out=[_obs(domain,"commoncrawl:count",len(urls))]
    out+=[_obs(domain,"commoncrawl",u) for u in list(dict.fromkeys(urls))[:limit]]
    return out

def virustotal_obs(domain: str, data: Dict[str,Any]) -> List[Observation]:
    attrs=((data or {}).get("data") or {}).get("attributes") or {}
    stats=attrs.get("last_analysis_stats") or {}
    if not stats: return []
    out=[_obs(domain,"virustotal:malicious",stats.get("malicious",0)),_obs(domain,"virustotal:suspicious",stats.get("suspicious",0))]
    if "reputation" in attrs: out.append(_obs(domain,"virustotal:reputation",attrs["reputation"]))
    return out

def threatfox_obs(domain: str, data: Dict[str,Any]) -> List[Observation]:
    if (data or {}).get("query_status")!="ok": return []
    return [_obs(domain,"threatfox",f"{r.get('malware_printable') or r.get('malware') or 'unknown'} ({r.get('threat_type') or 'n/a'})",notes=f"ioc={r.get('ioc','')}")
            for r in (data.get("data") or []) if isinstance(r,dict)]

def durable_obs(domain: str, scan_result: Dict[str,Any]) -> List[Observation]:
    """Identificadores duráveis (GA, GTM, AdSense, pixels) do scan: os artefatos raros que a Campaign Memory pesa mais."""
    ex=extract_durable_identifiers(scan_result)
    return [_obs(domain,"urlscan:durable_id",f"{i['type']}:{i['value']}") for i in ex["identifiers"]]

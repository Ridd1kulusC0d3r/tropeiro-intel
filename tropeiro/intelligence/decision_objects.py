def _band(v):
    if v>=.85:return "HIGH"
    if v>=.65:return "MODERATE"
    if v>=.40:return "LOW"
    return "INSUFFICIENT"

def build_ioc_decisions(iocs, warning_engine=None):
    out=[]
    for x in iocs:
        conf=float(x.get("confidence",0)); warnings=warning_engine.check(x.get("value"),x.get("context",{})) if warning_engine else []
        penalty=warning_engine.actionability_penalty(warnings) if warning_engine else 0; actionable=max(0,conf-penalty); active=bool(x.get("active",False)); mutable=x.get("type") in {"ip","url"}
        low_fp=actionable>=.80 and not any(w["severity"]=="high" for w in warnings)
        out.append({"ioc":x.get("value"),"ioc_type":x.get("type"),"campaign":x.get("campaign"),"confidence":round(conf,3),"confidence_band":_band(conf),"actionability":round(actionable,3),"severity":x.get("severity","medium"),"first_seen":x.get("first_seen"),"last_seen":x.get("last_seen"),"active_now":active,"evidence_count":int(x.get("evidence_count",0)),"independent_sources":int(x.get("source_families",0)),"false_positive_risk":"LOW" if low_fp else ("MEDIUM" if actionable>=.55 else "HIGH"),"block_recommended":bool(active and actionable>=.80 and x.get("type") in {"domain","url"}),"hunt_recommended":bool(actionable>=.55),"takedown_candidate":bool(active and actionable>=.75 and x.get("type") in {"domain","url"}),"monitor_recommended":bool(.35<=actionable<.80 or mutable),"expiration_guidance":"revalidate_24h" if mutable else "revalidate_7d","warning_hits":warnings,"rationale":x.get("rationale",[])})
    return sorted(out,key=lambda x:(x["actionability"],x["evidence_count"]),reverse=True)

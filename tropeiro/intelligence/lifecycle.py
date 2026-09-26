from datetime import datetime, timezone

def _dt(v):
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(timezone.utc)
    except:return None

def infer_campaign_lifecycle(events, now=None):
    now=now or datetime.now(timezone.utc);times=[_dt(x.get("observed_at") or x.get("timestamp")) for x in events];times=[x for x in times if x]
    if not times:return {"stage":"UNKNOWN","confidence":"INSUFFICIENT","reason":"No temporal evidence."}
    first,last=min(times),max(times);days_since=(now-last).total_seconds()/86400;span=(last-first).total_seconds()/86400;recent=sum(1 for x in times if (now-x).total_seconds()<=48*3600)
    if days_since>30:stage="DORMANT"
    elif days_since>7:stage="DECAY"
    elif recent>=3 and span>=1:stage="ACTIVE_EXPANDING"
    elif recent>=1:stage="ACTIVE"
    else:stage="STAGING"
    return {"stage":stage,"first_seen":first.isoformat(),"last_seen":last.isoformat(),"observations":len(times),"recent_48h":recent,"confidence":"MODERATE" if len(times)<3 else "HIGH"}

def infrastructure_churn(observations):
    domains=set();ips=set();certs=set();ns=set()
    for x in observations:
        typ=x.get("entity_type") or x.get("type");val=x.get("entity") or x.get("value");source=str(x.get("source",""))
        if typ=="domain":domains.add(val)
        elif typ=="ip":ips.add(val)
        elif typ=="certificate":certs.add(val)
        if "NS" in source.upper():ns.add(str(x.get("value","")))
    d=max(1,len(domains));ratio=(len(ips)+len(certs))/d;level="HIGH" if ratio>=2 else ("MEDIUM" if ratio>=.8 else "LOW");durable=[]
    if ns:durable.append("nameserver")
    if certs and len(certs)<len(domains):durable.append("certificate")
    return {"churn_level":level,"domains":len(domains),"ips":len(ips),"certificates":len(certs),"ns_values":len(ns),"change_ratio":round(ratio,3),"potential_durable_pivots":durable}

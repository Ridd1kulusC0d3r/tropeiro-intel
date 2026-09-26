from datetime import datetime, timezone

def _dt(v):
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception:return None

def infer_campaign_lifecycle(events,now=None,previous_last_seen=None):
    now=now or datetime.now(timezone.utc);times=[_dt(x.get('observed_at') or x.get('timestamp')) for x in events];times=sorted(x for x in times if x)
    if not times:return {'stage':'UNKNOWN','confidence':'INSUFFICIENT','reason':'No temporal evidence.'}
    first,last=min(times),max(times);age=(now-last).total_seconds()/86400;span=(last-first).total_seconds()/86400
    recent24=sum(1 for x in times if (now-x).total_seconds()<=86400);recent72=sum(1 for x in times if (now-x).total_seconds()<=72*3600)
    gap=max([(b-a).total_seconds()/86400 for a,b in zip(times,times[1:])] or [0])
    prev=_dt(previous_last_seen)
    if prev and (last-prev).total_seconds()/86400>14 and recent72:stage='REACTIVATED';reason='Recent observations followed a long prior quiet period.'
    elif age>30:stage='DORMANT';reason='No recent observation for more than 30 days.'
    elif age>7:stage='DECAY';reason='Last observation is older than one week.'
    elif recent72>=5 and span>=1:stage='EXPANSION';reason='Multiple recent observations across an expanding time window.'
    elif recent24>=1 and len(times)>=2:stage='ACTIVE';reason='Current observations support ongoing activity.'
    elif len(times)>=2:stage='STAGING';reason='Infrastructure observed but current operational activity is not firmly established.'
    else:stage='PREPARATION';reason='Single early observation; operational state remains uncertain.'
    return {'stage':stage,'first_seen':first.isoformat(),'last_seen':last.isoformat(),'observations':len(times),'recent_24h':recent24,'recent_72h':recent72,'largest_gap_days':round(gap,2),'confidence':'HIGH' if len(times)>=5 else 'MODERATE' if len(times)>=2 else 'LOW','reason':reason}

def infrastructure_churn(observations):
    domains=set();ips=set();certs=set();ns=set();mx=set();redirects=set()
    for x in observations:
        typ=x.get('entity_type') or x.get('type');val=x.get('entity') or x.get('value');source=str(x.get('source','')).lower();v=str(x.get('value',''))
        if typ=='domain':domains.add(val)
        elif typ=='ip':ips.add(val)
        elif typ=='certificate':certs.add(val)
        if 'dns:ns' in source or source.endswith(':ns'):ns.add(v)
        if 'dns:mx' in source or source.endswith(':mx'):mx.add(v)
        if 'redirect' in source:redirects.add(v)
    d=max(1,len(domains));ratio=(len(ips)+len(certs)+len(ns)+len(redirects))/d
    level='HIGH' if ratio>=3 else 'MEDIUM' if ratio>=1.2 else 'LOW'
    return {'churn_level':level,'domains':len(domains),'ips':len(ips),'certificates':len(certs),'nameservers':len(ns),'mx_values':len(mx),'redirects':len(redirects),'change_ratio':round(ratio,3)}

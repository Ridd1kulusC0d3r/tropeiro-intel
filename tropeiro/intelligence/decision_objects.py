DEFAULT_POLICY={'block_actionability':.85,'takedown_actionability':.78,'hunt_actionability':.55,'min_block_sources':2,'min_block_evidence':3}
def _band(v):
    if v>=.85:return 'HIGH'
    if v>=.65:return 'MODERATE'
    if v>=.40:return 'LOW'
    return 'INSUFFICIENT'

def build_ioc_decisions(iocs,warning_engine=None,policy=None):
    p={**DEFAULT_POLICY,**(policy or {})};out=[]
    for x in iocs:
        conf=max(0,min(1,float(x.get('confidence',0) or 0)));warnings=warning_engine.check(x.get('value'),x.get('context',{})) if warning_engine else [];penalty=warning_engine.actionability_penalty(warnings) if warning_engine else 0
        actionable=max(0,conf-penalty);active=bool(x.get('active',False));typ=x.get('type');src=int(x.get('source_families',0));ev=int(x.get('evidence_count',0));high_warning=any(w.get('severity')=='high' for w in warnings)
        can_block=bool(active and actionable>=p['block_actionability'] and typ in {'domain','url'} and src>=p['min_block_sources'] and ev>=p['min_block_evidence'] and not high_warning)
        hunt=bool(actionable>=p['hunt_actionability']);takedown=bool(active and actionable>=p['takedown_actionability'] and typ in {'domain','url'} and src>=2)
        if can_block:decision='BLOCK'
        elif takedown:decision='TAKEDOWN_CANDIDATE'
        elif hunt:decision='HUNT'
        elif actionable>=.35:decision='MONITOR'
        elif warnings:decision='DO_NOT_BLOCK'
        else:decision='INSUFFICIENT_EVIDENCE'
        out.append({'ioc':x.get('value'),'ioc_type':typ,'campaign':x.get('campaign'),'confidence':round(conf,3),'confidence_band':_band(conf),'actionability':round(actionable,3),'severity':x.get('severity','medium'),'first_seen':x.get('first_seen'),'last_seen':x.get('last_seen'),'active_now':active,'evidence_count':ev,'independent_sources':src,'false_positive_risk':'LOW' if can_block else ('MEDIUM' if actionable>=.55 and not high_warning else 'HIGH'),'decision':decision,'block_recommended':can_block,'hunt_recommended':hunt,'takedown_candidate':takedown,'monitor_recommended':decision=='MONITOR','expiration_guidance':'revalidate_24h' if typ in {'ip','url'} else 'revalidate_7d','warning_hits':warnings,'rationale':x.get('rationale',[])})
    return sorted(out,key=lambda x:(x['actionability'],x['evidence_count']),reverse=True)

def build_action_matrix(decisions, collection_gaps=None, detection_package=None):
    actions=[]
    for d in decisions:
        ioc=d["ioc"]; typ=d["ioc_type"]
        if d.get("block_recommended"):
            actions.append({"priority":"P1","action":"BLOCK","target":ioc,"target_type":typ,"owner":"SOC / Network Security","why":f"Active high-actionability IOC ({d['actionability']:.2f}); FP risk {d['false_positive_risk']}.","evidence_required":"Preserve evidence ledger and decision object before enforcement."})
        if d.get("hunt_recommended"):
            actions.append({"priority":"P1" if d["actionability"]>=.75 else "P2","action":"HUNT","target":ioc,"target_type":typ,"owner":"SOC / Detection Engineering","why":"Search historical telemetry for exposure and related activity.","evidence_required":"DNS/proxy/email/identity telemetry as applicable."})
        if d.get("takedown_candidate"):
            actions.append({"priority":"P1","action":"TAKEDOWN_PREP","target":ioc,"target_type":typ,"owner":"Threat Intel / Brand Protection","why":"Active phishing candidate with sufficient evidence for abuse-package preparation.","evidence_required":"RDAP, hosting/registrar, timestamps, public scan evidence, campaign linkage."})
        if d.get("monitor_recommended") and not d.get("block_recommended"):
            actions.append({"priority":"P2","action":"MONITOR","target":ioc,"target_type":typ,"owner":"Threat Intel","why":"Indicator is mutable, shared, or confidence is below enforcement threshold.","evidence_required":"Revalidation and temporal observations."})
    for g in (collection_gaps or []):
        if g.get("priority")=="P1":
            actions.append({"priority":"P1","action":"COLLECT","target":g["gap"],"target_type":"intelligence_gap","owner":"Threat Intel / OSINT","why":g.get("impact","Gap blocks a higher-confidence judgment."),"evidence_required":g.get("recommended_collection","")})
    order={"P1":0,"P2":1,"P3":2}
    return sorted(actions,key=lambda x:(order.get(x["priority"],9),x["action"],str(x["target"])))

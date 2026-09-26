TYPE_DISCRIMINATION={"tracker":1.00,"public_contact":.95,"certificate":.90,"redirect":.88,"jarm":.72,"nameserver":.60,"mx":.58,"domain":.55,"ip":.35,"asn":.18,"provider":.10}

def rank_pivots(candidates):
    out=[]
    for c in candidates:
        discr=float(c.get("discrimination",TYPE_DISCRIMINATION.get(c.get("type"),.4)));ev=float(c.get("evidence_value",.5));novelty=float(c.get("novelty",.5));rel=float(c.get("source_reliability",.7));noise=max(.05,float(c.get("expected_noise",.5)));utility=(discr*ev*novelty*rel)/noise;rc=max(0,int(c.get("result_count",0) or 0))
        if rc>1000:utility*=.25
        elif rc>100:utility*=.55
        elif rc>25:utility*=.8
        out.append({**c,"utility":round(utility,4)})
    return sorted(out,key=lambda x:x["utility"],reverse=True)

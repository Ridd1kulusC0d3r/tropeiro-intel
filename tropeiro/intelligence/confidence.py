def _band(v):
    v=float(v or 0)
    if v>=.85: return "HIGH"
    if v>=.65: return "MODERATE"
    if v>=.40: return "LOW"
    return "INSUFFICIENT"

def multidimensional_confidence(infrastructure_relationship=0,common_operator=0,malicious_intent=0,campaign_active=0,victimology=0,identity_attribution=0):
    vals={"infrastructure_relationship":float(infrastructure_relationship),"common_operator":float(common_operator),"malicious_intent":float(malicious_intent),"campaign_active":float(campaign_active),"victimology":float(victimology),"identity_attribution":float(identity_attribution)}
    return {k:{"score":round(v,3),"band":_band(v)} for k,v in vals.items()}

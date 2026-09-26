from collections import defaultdict
from math import prod
from .hypotheses import assess_hypotheses

EVIDENCE_WEIGHTS = {
    "same_phone":1.00,
    "same_email":1.00,
    "same_tracker":0.95,
    "same_registrant_org":0.90,
    "same_certificate":0.85,
    "same_redirect_chain":0.80,
    "same_html_fingerprint":0.75,
    "same_jarm":0.65,
    "same_ns_pair":0.55,
    "same_mx":0.50,
    "same_registrar_pattern":0.45,
    "same_asn":0.30,
    "same_ip":0.25,
    "same_provider":0.10,
}

def evidence_score(evidence):
    """Combine independent signals conservatively. Returns correlation confidence, not actor guilt."""
    vals=[]
    families=set()
    strong=0
    for e in evidence:
        w=EVIDENCE_WEIGHTS.get(e.get("code"),0.0)
        reliability=float(e.get("source_reliability",1.0))
        vals.append(max(0,min(.98,w*reliability)))
        families.add(e.get("source_family") or e.get("source") or "unknown")
        if w >= .75:
            strong += 1
    combined = 1-prod((1-v) for v in vals) if vals else 0.0
    if len(families) < 2:
        combined=min(combined,.59)
    if strong == 0:
        combined=min(combined,.69)
    return round(combined,4), len(families), strong

def confidence_band(score):
    if score >= .85: return "HIGH"
    if score >= .65: return "MODERATE"
    if score >= .40: return "LOW"
    return "INSUFFICIENT"

def attribution_level(score, strong, independent_families, identity_evidence=False, known_actor_evidence=False):
    if score < .40: return 1
    if score < .65: return 2
    if score < .85 or strong < 2 or independent_families < 2: return 3
    if identity_evidence:
        return 5 if known_actor_evidence and independent_families >= 3 else 4
    return 3

class AttributionEngine:
    """Produces assessments of common operational control without equating correlation to identity."""
    def assess(self, left, right, evidence, infrastructure_owner=None,
               registration_entity=None, identity_evidence=False, known_actor_evidence=False):
        score,families,strong=evidence_score(evidence)
        level=attribution_level(score,strong,families,identity_evidence,known_actor_evidence)
        return {
            "left":left,"right":right,
            "common_operator_score":score,
            "common_operator_confidence":confidence_band(score),
            "attribution_level":level,
            "independent_source_families":families,
            "strong_evidence_count":strong,
            "infrastructure_owner":infrastructure_owner,
            "registration_entity":registration_entity,
            "identity_attribution":"SUPPORTED" if identity_evidence and level>=4 else "INSUFFICIENT_EVIDENCE",
            "known_actor_attribution":"SUPPORTED" if known_actor_evidence and level>=5 else "NOT_ESTABLISHED",
            "evidence":evidence,
            "competing_hypotheses":assess_hypotheses([e.get("code") for e in evidence]),
            "caveat":"Correlation confidence is not proof of criminal identity or intent."
        }

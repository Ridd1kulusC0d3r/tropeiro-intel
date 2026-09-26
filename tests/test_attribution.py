from tropeiro.attribution.engine import AttributionEngine, evidence_score
from tropeiro.attribution.entity_resolution import canonical_org, protected_identifier

def test_canonical_org():
    assert canonical_org("ACME Tecnologia LTDA.") == "acme tecnologia"

def test_protected_identifier():
    assert protected_identifier("a@example.com") == protected_identifier("A@example.com")

def test_single_weak_family_capped():
    s,f,strong=evidence_score([
        {"code":"same_ip","source_family":"hosting","source_reliability":1.0},
        {"code":"same_asn","source_family":"hosting","source_reliability":1.0},
    ])
    assert s <= .59
    assert f == 1

def test_multisource_operator_assessment():
    ev=[
        {"code":"same_email","source_family":"registration","source_reliability":.95},
        {"code":"same_tracker","source_family":"web","source_reliability":.90},
        {"code":"same_certificate","source_family":"tls","source_reliability":.90},
    ]
    a=AttributionEngine().assess("CAMP-1","CAMP-2",ev)
    assert a["common_operator_confidence"] in {"MODERATE","HIGH"}
    assert a["independent_source_families"] == 3

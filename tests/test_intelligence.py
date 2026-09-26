from tropeiro.intelligence.warninglists import WarningListEngine
from tropeiro.intelligence.decision_objects import build_ioc_decisions
from tropeiro.intelligence.pivot import rank_pivots
from tropeiro.intelligence.collection_gap import build_collection_gaps
from tropeiro.intelligence.lifecycle import infer_campaign_lifecycle
from tropeiro.intelligence.victimology import infer_victimology
from tropeiro.intelligence.objectives import infer_objectives

def test_warninglist_penalizes_public_resolver():
    w=WarningListEngine()
    hits=w.check("8.8.8.8",{})
    assert hits and hits[0]["type"]=="public_dns_resolver"

def test_shared_warning_prevents_block():
    w=WarningListEngine()
    d=build_ioc_decisions([{
        "value":"8.8.8.8","type":"ip","confidence":.99,"active":True,
        "context":{},"source_families":3,"evidence_count":5
    }],w)[0]
    assert d["block_recommended"] is False
    assert d["false_positive_risk"]!="LOW"

def test_pivot_prefers_discriminating_identifier():
    rows=rank_pivots([
        {"value":"AS1","type":"asn","evidence_value":.7,"novelty":.7,"source_reliability":.9,"expected_noise":.9,"result_count":5000},
        {"value":"UA-123","type":"tracker","evidence_value":.8,"novelty":.9,"source_reliability":.8,"expected_noise":.2,"result_count":9},
    ])
    assert rows[0]["type"]=="tracker"

def test_collection_gaps_include_redirect():
    g=build_collection_gaps({"active_state_known":True,"registration_entity_known":True,
        "redirect_chain_known":False,"credential_endpoint_known":True,"victimology_known":True,
        "operator_identity_known":False,"independent_source_families":2})
    assert any(x["gap"]=="redirect_chain" for x in g)

def test_victimology_ptbr_banking():
    v=infer_victimology("Sua conta PIX foi bloqueada. regularize seu banco", "Banco X")
    assert v["language"]=="pt-BR"
    assert "banking" in v["likely_sectors"]

def test_objective_credentials():
    o=infer_objectives("Acesse o login e verifique sua senha")
    assert o["primary"]=="credential_theft"

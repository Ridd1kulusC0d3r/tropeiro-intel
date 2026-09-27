import copy
from tropeiro.ai import extract_gliner_entities,build_evidence_packet,validate_ai_analysis,attach_ai_overlay,parse_json_response

class FakeGLiNER:
    def predict_entities(self,text,labels,threshold=.45):
        return [{"text":"Banco Exemplo","label":"organization","score":.91,"start":0,"end":13}]

def sample_report():
    return {"meta":{"case_id":"AI-1"},"evidence_ledger":[{"evidence_id":"EV-1","entity":"x.test","source":"dns","value":"1.2.3.4"}],"ioc_decisions":[{"ioc":"x.test","decision":"HUNT"}],"source_status":[{"source":"dns","status":"OK"}]}

def test_gliner_candidate_only():
    rows=extract_gliner_entities([{"source":"lure","text":"Banco Exemplo"}],FakeGLiNER())
    assert rows[0]["derived"] is True and rows[0]["analyst_confirmed"] is False

def test_packet_does_not_mutate():
    report=sample_report();before=copy.deepcopy(report);packet=build_evidence_packet(report)
    assert report==before and packet["packet_sha256"]

def test_unknown_refs_removed():
    packet=build_evidence_packet(sample_report())
    result=validate_ai_analysis({"key_findings":[{"statement":"x","evidence_refs":["EV-1","EV-FAKE"]}]},packet)
    assert result["key_findings"][0]["evidence_refs"]==["EV-1"]
    assert result["_validation"]["warnings"]

def test_overlay_preserves_evidence():
    report=sample_report();before=copy.deepcopy(report["evidence_ledger"])
    out=attach_ai_overlay(report,entities=[{"value":"x"}],analysis={"executive_summary":"x"})
    assert out["evidence_ledger"]==before and report["evidence_ledger"]==before

def test_json_recovery():
    x=parse_json_response('prefix {"executive_summary":"ok"} suffix')
    assert x["data"]["executive_summary"]=="ok"

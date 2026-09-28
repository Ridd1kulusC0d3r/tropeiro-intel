from tropeiro.memory import CaseMemory, extract_case_artifacts


def report(case_id, domain, ip, tracker=None, registrant=None):
    durable = [{"kind": "gtm", "value": tracker}] if tracker else []
    return {
        "meta": {"case_id": case_id, "version": "test", "analyst": "A", "mode": "PASSIVE"},
        "ioc_decisions": [{"ioc": domain, "ioc_type": "domain"}],
        "ownership": {
            domain: {
                "dns": {"A": [ip], "NS": ["ns.shared.example"], "MX": [], "CNAME": []},
                "rdap": {
                    "registrant_orgs": [registrant] if registrant else [],
                    "registrar_orgs": ["Common Registrar"],
                },
                "cert_names": [domain],
            }
        },
        "durable_identifiers": durable,
        "evidence_ledger": [],
    }


def test_memory_store_and_stats(tmp_path):
    m = CaseMemory(tmp_path / "m.sqlite")
    x = m.store_case(report("C1", "one.test", "1.2.3.4", "GTM-RARE"))
    assert x["artifacts"] > 0
    assert m.stats()["cases"] == 1
    assert m.list_cases()[0]["case_id"] == "C1"


def test_cross_case_similarity_is_explainable(tmp_path):
    m = CaseMemory(tmp_path / "m.sqlite")
    m.store_case(report("C1", "one.test", "1.2.3.4", "GTM-SHARED", "Org X"))
    m.store_case(report("C2", "two.test", "1.2.3.4", "GTM-SHARED", "Org X"))
    current = report("C3", "three.test", "1.2.3.4", "GTM-SHARED", "Org X")
    matches = m.compare_report(current, exclude_case_id="C3")
    assert matches
    assert matches[0]["shared_discriminating"] >= 1
    assert matches[0]["top_contributions"]
    assert matches[0]["same_operator_inferred"] is False


def test_common_ip_alone_is_capped(tmp_path):
    m = CaseMemory(tmp_path / "m.sqlite")
    m.store_case(report("C1", "one.test", "9.9.9.9"))
    current = report("C2", "two.test", "9.9.9.9")
    matches = m.compare_report(current, exclude_case_id="C2")
    assert matches
    assert matches[0]["similarity_score"] <= .29


def test_ai_unconfirmed_not_memorized():
    r = {
        "meta": {"case_id": "A"},
        "ai_entities": [{"label": "domain", "value": "fake.test", "analyst_confirmed": False}],
    }
    assert not extract_case_artifacts(r)

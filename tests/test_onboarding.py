from tropeiro.onboarding import detect_input_type,input_label,requirements_for_input,recommended_features,budget_limits

def test_detect_common_input_types():
    assert detect_input_type("example.com") == "DOMAIN"
    assert detect_input_type("https://example.com/login") == "URL"
    assert detect_input_type("203.0.113.10") == "IP"
    assert detect_input_type("test@example.com") == "EMAIL"
    assert detect_input_type("a"*64) == "HASH"
    assert detect_input_type("example.com\n203.0.113.10") == "MULTI_IOC"

def test_dynamic_label():
    assert input_label("DOMAIN") == "Domínio"
    assert "E-mail" in input_label("EMAIL")

def test_domain_requirements_are_rich():
    req=requirements_for_input("DOMAIN")
    assert "dns" in req and "registration" in req and "tls" in req

def test_beginner_plan_stays_passive():
    f=recommended_features("DOMAIN",mode="PASSIVE",budget="free",secrets={})
    assert f["ENABLE_DNS"] is True
    assert f["ENABLE_HTTP_PROBE"] is False
    assert f["ENABLE_FOFA"] is False

def test_budget_limits_scale_down():
    assert budget_limits("balanced",20)["DNSTWIST_MAX"] < budget_limits("balanced",1)["DNSTWIST_MAX"]

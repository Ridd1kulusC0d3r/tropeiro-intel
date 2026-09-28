from tropeiro.frontend.app import relationship_rows, _normalize_target

def test_domain_input_normalization():
    kind,iocs=_normalize_target("example.com","AUTO")
    assert kind=="DOMAIN"
    assert "example.com" in iocs["domain"]

def test_relationship_rows():
    rows=relationship_rows({"example.com":{"dns":{"A":["1.2.3.4"],"MX":["mail.example.net"]},"rdap":{"registrant_orgs":["Example Org"]},"cert_names":["www.example.com"]}})
    kinds={x["relationship"] for x in rows}
    assert "dns_a" in kinds
    assert "registrant_org" in kinds
    assert "certificate_name" in kinds

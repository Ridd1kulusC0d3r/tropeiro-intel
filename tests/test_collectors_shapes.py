from tropeiro.collectors.dnsdumpster import normalize

def test_dnsdumpster_normalize():
    p={"a":[{"host":"x.example","ip":"1.2.3.4","asn":"AS64500","asn_name":"Example Net","netblock":"1.2.3.0/24"}]}
    r=normalize("example.com",p)
    assert r["records"][0]["ip"]=="1.2.3.4"
    assert "Example Net" in r["asn_owners"]

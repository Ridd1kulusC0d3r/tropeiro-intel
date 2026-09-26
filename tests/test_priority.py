from tropeiro.hunting.priority import prioritize

def test_priority_explainable():
    p,reasons=prioritize('brand-login.example','brand',has_mx=True)
    assert 0 <= p <= 100
    assert isinstance(reasons,list)

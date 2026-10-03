import pytest
from tropeiro.targets import classify, parse_target, registrable

CASES={
 'example.com':'DOMAIN','https://example.com/login?x=1':'URL','1.1.1.1':'IP','2606:4700:4700::1111':'IP','alguem@example.com':'EMAIL',
 'd41d8cd98f00b204e9800998ecf8427e':'HASH','+55 11 99999-0000':'PHONE','11999990000':'PHONE','example[.]com':'DOMAIN','hxxps://x[.]com/a':'URL',
 'example.com\nexample.org':'DOMAIN','example.com; example.org':'DOMAIN','example.com, 1.1.1.1':'MULTI_IOC','asdf qwerty':'LURE_TEXT',
 'Olá, clique em http://x.com':'LURE_TEXT','':'AUTO','1234':'LURE_TEXT',
 'Receita Federal: regularize seu CPF em hxxps://receita-regulariza[.]example/cpf ou https://wa.me/5511999990000. Banco Aurora S.A.':'LURE_TEXT',
}

@pytest.mark.parametrize('text,kind',list(CASES.items()))
def test_classify(text,kind):
    assert classify(text)==kind

def test_lure_with_digits_is_not_a_phone():
    """Bug real: texto com 13 dígitos (o número do WhatsApp) era classificado como TELEFONE e nenhuma fonte rodava."""
    t=parse_target(list(CASES)[-1])
    assert t.kind=='LURE_TEXT' and t.domains==['receita-regulariza.example'] and t.skipped_legit==['wa.me']

def test_parse_target_extracts_by_type():
    t=parse_target('Receita: hxxps://receita-fake[.]com/cpf ou https://wa.me/5511999990000. a@receita-fake.com IP 10.0.0.1 e 8.8.8.8')
    assert t.domains==['receita-fake.com'] and t.ips==['8.8.8.8']
    assert set(t.skipped_legit)=={'10.0.0.1','wa.me'}                      # privado e plataforma legítima: contexto
    assert t.lure_text and t.kinds_present=={'domain','ip'}

def test_email_collects_its_domain_and_phone_collects_nothing():
    e=parse_target('alguem@mail.example.co.uk'); assert e.kind=='EMAIL' and e.domains==['example.co.uk'] and e.iocs['email']==['alguem@mail.example.co.uk']
    p=parse_target('+55 11 99999-0000'); assert p.kind=='PHONE' and p.iocs['phone']==['5511999990000'] and not p.kinds_present

def test_registrable_handles_reserved_tlds():
    assert registrable('a1.example')=='a1.example' and registrable('login.example.co.uk')=='example.co.uk'

def test_manual_type_overrides_detection():
    assert parse_target('example.com','URL').kind=='URL'

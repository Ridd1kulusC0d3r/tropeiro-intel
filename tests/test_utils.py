from tropeiro.utils import extract_iocs, root_domain, defang

def test_extract():
    x=extract_iocs('Veja https://login.example.com/a e contato a@example.com e 8.8.8.8')
    assert 'https://login.example.com/a' in x['url']
    assert 'login.example.com' in x['domain']
    assert '8.8.8.8' in x['ip']

def test_root(): assert root_domain('https://a.b.example.com/x')=='example.com'
def test_defang(): assert 'example[.]com' in defang('https://example.com')

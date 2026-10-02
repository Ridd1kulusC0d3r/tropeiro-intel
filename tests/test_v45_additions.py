import json
from tropeiro.reporting.stix import bundle_from_iocs, validate
from tropeiro.reporting.misp import misp_event
from tropeiro.timeline import timeline_summary, timeline_markdown
from tropeiro.similarity.kit import kit_fingerprint, kit_similarity, cluster_kits
from tropeiro.correlation.registration import registration_batches
from tropeiro.intelligence.br_lures import detect_br_lures, extract_lure_infra, valid_cpf, valid_cnpj
from tropeiro.intelligence.sigma import sigma_rules

IOCS={'domain':['evil.example'],'ip':['203.0.113.9'],'url':['http://evil.example/a'],'email':['a@evil.example'],'hash':['a'*64]}

def test_stix_indicators_and_determinism():
    b1=bundle_from_iocs(IOCS,case_id='C1',confidence=70); b2=bundle_from_iocs(IOCS,case_id='C1',confidence=70)
    parsed=validate(b1.serialize())
    types=[o['type'] for o in parsed.objects]
    assert types.count('indicator')==4 and 'campaign' in types and 'relationship' in types
    ids=lambda b:sorted(o['id'] for o in b.objects if o['type']=='indicator')
    assert ids(b1)==ids(b2)
    ind=next(o for o in parsed.objects if o['type']=='indicator')
    assert ind['valid_until']>ind['valid_from'] and ind['confidence']==70

def test_stix_pattern_escapes_quotes():
    b=bundle_from_iocs({'url':["http://x.test/a'b"]})
    assert "a\\'b" in next(o for o in b.objects if o['type']=='indicator')['pattern']

def test_misp_ids_policy_and_hash_types():
    ev=misp_event('C1',{**IOCS,'hash':['b'*32],'phone':['11999990000']})['Event']
    by={a['type']:a for a in ev['Attribute']}
    assert by['domain']['to_ids'] is True and by['email-dst']['to_ids'] is False
    assert by['phone-number']['to_ids'] is False and 'md5' in by
    assert {'name':'tlp:amber'} in ev['Tag']

def test_timeline_summary():
    ev=[{'entity':'a.test','observed_at':'2026-01-02','source':'crtsh'},{'entity':'a.test','observed_at':'2026-01-01','source':'rdap'}]
    s=timeline_summary(ev)['a.test']
    assert s['first_seen']=='2026-01-01' and s['sources']==['crtsh','rdap'] and s['observations']==2
    assert '`a.test`' in timeline_markdown(ev)

def test_kit_similarity_and_cluster():
    a={'index.html':b'x','js/app.js':b'y','img/logo.png':b'z'}
    b={'index.html':b'x','js/app.js':b'y','img/logo.png':b'z','extra.txt':b'q'}
    c={'other.html':b'1'}
    assert kit_fingerprint(a)==kit_fingerprint(dict(reversed(list(a.items()))))
    assert kit_similarity(a,b)==0.75 and kit_similarity(a,c)==0
    assert cluster_kits({'d1':a,'d2':b,'d3':c})==[['d1','d2']]

def test_registration_batches():
    rows=[{'domain':f'd{i}.test','created':f'2026-03-01T10:00:{i*10:02d}Z','registrar':'R','nameservers':['ns1.x']} for i in range(3)]
    rows.append({'domain':'late.test','created':'2026-03-05T10:00:00Z','registrar':'R','nameservers':['ns1.x']})
    out=registration_batches(rows)
    assert len(out)==1 and out[0]['domains']==['d0.test','d1.test','d2.test']

def test_br_lures_and_validators():
    assert valid_cpf('529.982.247-25') and not valid_cpf('111.111.111-11') and not valid_cpf('529.982.247-24')
    assert valid_cnpj('11.222.333/0001-81') and not valid_cnpj('11.222.333/0001-82')
    txt='Receita Federal: regularize seu CPF 529.982.247-25 ou fale em https://wa.me/5511999990000 chave 123e4567-e89b-12d3-a456-426614174000'
    assert detect_br_lures(txt)[0]['brand']=='Receita Federal'
    out=extract_lure_infra(txt)
    assert out['cpf']==['52998224725'] and out['whatsapp']==['5511999990000'] and out['pix_evp']
    assert 'cnpj' not in out

def test_sigma_rules_drop_invalid_domains():
    r=sigma_rules({'domain':['evil.example','bad/../x'],'ip':['203.0.113.9']},'C1')
    assert "'evil.example'" in r['dns'] and 'bad/' not in r['dns'] and "'203.0.113.9'" in r['network']
    assert sigma_rules({},'C1')=={}

def test_calibration_report():
    from tropeiro.intelligence.calibration import calibration_report
    r=calibration_report([(0.9,1),(0.8,1),(0.2,0),(0.1,0),(0.7,0)])
    assert r['cases']==5 and r['brier']<0.25 and r['reliability']

def test_cli_lure_exports(tmp_path,capsys):
    from tropeiro.cli import main
    f=tmp_path/'l.txt'; f.write_text('Correios: taxa pendente https://evil.example/p',encoding='utf-8')
    assert main(['lure',str(f),'--case','C9','--out',str(tmp_path/'o')])==0
    assert {p.name for p in (tmp_path/'o').iterdir()}>={'stix.json','misp.json','sigma_dns.yml'}
    assert 'Correios' in capsys.readouterr().out

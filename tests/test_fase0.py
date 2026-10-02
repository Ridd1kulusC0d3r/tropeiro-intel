"""Fase 0: Workbench respeita modo/profundidade, enriquecimentos, lotes de registro e iscas parecidas."""
import json, zipfile
import pytest
from tropeiro.frontend import app as fe, enrich
from tropeiro.frontend.demo import DEMO_LURE

def test_enrichers():
    wb=enrich.wayback_obs('a.example',[['http://a.example/x','20260920103000','200'],['http://a.example/y','20260925080000','200']])
    d={(o.source,o.value) for o in wb}
    assert ('wayback:count','2') in d and ('wayback:first_seen','2026-09-20T10:30:00+00:00') in d and ('wayback','http://a.example/x') in d
    assert enrich.wayback_obs('a.example',[])==[]
    assert {o.value for o in enrich.commoncrawl_obs('a.example',[{'url':'http://a.example/p'}]) if o.source=='commoncrawl'}=={'http://a.example/p'}
    vt=enrich.virustotal_obs('a.example',{'data':{'attributes':{'last_analysis_stats':{'malicious':7,'suspicious':1},'reputation':-12}}})
    assert {(o.source,o.value) for o in vt}=={('virustotal:malicious','7'),('virustotal:suspicious','1'),('virustotal:reputation','-12')}
    assert enrich.virustotal_obs('a.example',{})==[]
    tf=enrich.threatfox_obs('a.example',{'query_status':'ok','data':[{'malware_printable':'Mispadu','threat_type':'botnet_cc','ioc':'a.example'}]})
    assert tf[0].value=='Mispadu (botnet_cc)' and enrich.threatfox_obs('a.example',{'query_status':'no_result'})==[]
    ids=enrich.durable_obs('a.example',{'page':{'title':'x'},'body':'ga UA-1234567-1 and GTM-ABCDE1'})
    assert {o.value for o in ids}=={'google_analytics:UA-1234567-1','google_tag_manager:GTM-ABCDE1'}

@pytest.fixture
def calls(monkeypatch,tmp_path):
    """Substitui todas as fontes e conta as chamadas."""
    log=[]
    def rec(name,ret):
        def f(*a,**k): log.append(name); return ret(a) if callable(ret) else ret
        return f
    monkeypatch.setattr(fe.tempfile,'gettempdir',lambda:str(tmp_path))
    monkeypatch.setenv('HOME',str(tmp_path))
    monkeypatch.setattr(fe.dns,'query',rec('dns',['203.0.113.17']))
    monkeypatch.setattr(fe.rdap,'lookup',rec('rdap',lambda a:{'created':'2026-09-20T10:00:00Z','registrar_orgs':['R'],'nameservers':['ns1.x']}))
    monkeypatch.setattr(fe.crtsh,'lookup',rec('crtsh',[]))
    monkeypatch.setattr(fe.urlscan,'search',rec('urlscan',{'results':[{'_id':f's{i}','page':{'url':f'http://x/{i}'}} for i in range(20)]}))
    monkeypatch.setattr(fe.urlscan,'result',rec('urlscan_result',{'body':'UA-1234567-1'}))
    monkeypatch.setattr(fe.threatintel,'otx_domain',rec('otx',{}))
    monkeypatch.setattr(fe.history,'wayback',rec('wayback',[['http://x/a','20260920103000','200']]))
    monkeypatch.setattr(fe.history,'commoncrawl',rec('commoncrawl',[{'url':'http://x/cc'}]))
    monkeypatch.setattr(fe.threatintel,'virustotal_domain',rec('vt',{'data':{'attributes':{'last_analysis_stats':{'malicious':3,'suspicious':0}}}}))
    monkeypatch.setattr(fe.threatintel,'threatfox_search',rec('threatfox',{'query_status':'no_result'}))
    for k in ('VT_API_KEY','THREATFOX_AUTH_KEY','URLSCAN_API_KEY'): monkeypatch.delenv(k,raising=False)
    return log

def run(**kw):
    kw.setdefault('memory_enabled',False)
    return fe.run_quick_case(kw.pop('target','novo.example'),kw.pop('kind','DOMAIN'),case_id=kw.pop('case_id','F0'),**kw)

def test_passive_balanced_runs_core_and_wayback_but_not_optional(calls):
    run()
    assert {'dns','rdap','crtsh','urlscan','otx','wayback'}<=set(calls)
    assert not {'commoncrawl','vt','threatfox'}&set(calls)

def test_safe_enrichment_adds_commoncrawl(calls):
    run(mode='SAFE_ENRICHMENT')
    assert 'commoncrawl' in calls

def test_optional_keys_enable_vt_and_threatfox(calls,monkeypatch):
    monkeypatch.setenv('VT_API_KEY','k'); monkeypatch.setenv('THREATFOX_AUTH_KEY','k')
    res=run()
    assert {'vt','threatfox'}<=set(calls)
    assert any(e['source']=='virustotal:malicious' and e['value']=='3' for e in res['evidence'])

@pytest.mark.parametrize('budget,expected',[('free',5),('balanced',12),('extended',20)])
def test_budget_limits_urlscan_detail_fetches(calls,budget,expected):
    run(budget=budget)
    assert calls.count('urlscan_result')==expected            # extended: 30 permitidos, mas só há 20 scans

def test_durable_identifiers_reach_the_ledger(calls):
    res=run()
    assert any(e['source']=='urlscan:durable_id' and e['value']=='google_analytics:UA-1234567-1' for e in res['evidence'])

def test_registration_batches_for_multi_ioc(calls):
    res=run(target='a1-phish.com\na2-phish.com\nb-phish.net',kind='MULTI_IOC')
    assert len(res['batches'])==1 and set(res['batches'][0]['domains'])=={'a1-phish.com','a2-phish.com','b-phish.net'}
    assert fe.batch_rows(res['batches'])[0]['motivo']

def test_similar_lures_via_memory_and_lure_text_not_exported(calls,tmp_path):
    mem=str(tmp_path/'m.sqlite')
    first=run(target=DEMO_LURE,kind='LURE_TEXT',case_id='C-1',memory_enabled=True,memory_path=mem)
    assert first['similar_lures']==[]
    second=run(target=DEMO_LURE.replace('hoje','agora'),kind='LURE_TEXT',case_id='C-2',memory_enabled=True,memory_path=mem)
    assert [x['case_id'] for x in second['similar_lures']]==['C-1']
    z=zipfile.ZipFile(second['package_path']); case=json.loads(z.read('case.json'))
    assert 'lure_text' not in json.dumps(case)               # o texto fica só no banco local de memória


def test_legit_platforms_are_not_collected(calls,monkeypatch):
    queried=[]
    monkeypatch.setattr(fe.dns,'query',lambda d,*a,**k:queried.append(d) or [])
    run(target='Receita: hxxps://receita-fake[.]com/cpf e https://wa.me/5511999990000',kind='LURE_TEXT')
    assert set(queried)=={'receita-fake.com'}

"""Pipeline de ponta a ponta com fontes simuladas (sem rede): planejamento, estados, prazos, tipos de alvo."""
import json, time, urllib.error, io, zipfile
import pytest
from tropeiro import pipeline
from tropeiro.collectors import crtsh, dns, history, rdap, threatintel, urlscan
from tropeiro.frontend.demo import DEMO_LURE
from tropeiro.pipeline import investigate

class World:
    """Substitui todas as fontes por falsas e registra as chamadas."""
    def __init__(self,mp,tmp):
        self.calls=[]; self.mp=mp
        mp.setenv('TROPEIRO_WORKSPACE',str(tmp)); mp.setenv('HOME',str(tmp))
        for k in ('VT_API_KEY','THREATFOX_AUTH_KEY','URLSCAN_API_KEY','DNSDUMPSTER_API_KEY','FOFA_API_KEY','CENSYS_PAT'): mp.delenv(k,raising=False)
        self.set(dns,'query',lambda d,t='A':['203.0.113.17'] if t=='A' else [])
        self.set(dns,'reverse_ptr',['host.example.net'])
        self.set(rdap,'lookup',{'created':'2026-09-20T10:00:00Z','registrar_orgs':['R'],'registrant_orgs':[],'nameservers':['ns1.x']})
        self.set(rdap,'lookup_ip',{'name':'NET-1','country':'US','type':'ALLOCATED','start':'203.0.113.0','end':'203.0.113.255','orgs':['Org Exemplo']})
        self.set(crtsh,'lookup',[{'name_value':'www.novo-dominio.com\nnovo-dominio.com'}])
        self.set(urlscan,'search',{'results':[{'_id':f's{i}','page':{'url':f'http://x/{i}'}} for i in range(20)]})
        self.set(urlscan,'search_ip',{'results':[{'page':{'url':'http://a.example/x','domain':'a.example'}},{'page':{'url':'http://b.example/y','domain':'b.example'}}]})
        self.set(urlscan,'result',{'body':'UA-1234567-1'})
        self.set(threatintel,'otx_domain',{'url_list':[{'url':'http://x/otx'}]})
        self.set(history,'wayback',[['http://x/a','20260920103000','200']])
        self.set(history,'commoncrawl',[{'url':'http://x/cc'}])
        self.set(threatintel,'virustotal_domain',{'data':{'attributes':{'last_analysis_stats':{'malicious':3,'suspicious':0}}}})
        self.set(threatintel,'virustotal_ip',{'data':{'attributes':{'last_analysis_stats':{'malicious':0,'suspicious':0}}}})
        self.set(threatintel,'virustotal_file',{'data':{'attributes':{'last_analysis_stats':{'malicious':9,'suspicious':1}}}})
        self.set(threatintel,'threatfox_search',{'query_status':'no_result'})
    def set(self,mod,name,ret):
        label=f'{mod.__name__.rsplit(".",1)[-1]}.{name}'
        def f(*a,**k):
            self.calls.append(label if not a else (label,a[0]))
            if callable(ret): return ret(*a,**k)
            return ret
        self.mp.setattr(mod,name,f)
    def names(self): return {c if isinstance(c,str) else c[0] for c in self.calls}
    def count(self,label): return sum(1 for c in self.calls if (c if isinstance(c,str) else c[0])==label)

@pytest.fixture
def world(monkeypatch,tmp_path): return World(monkeypatch,tmp_path)

def run(t='novo-dominio.com',**kw):
    kw.setdefault('memory_enabled',False); kw.setdefault('use_cache',False); kw.setdefault('case_id','T1')
    return investigate(t,**kw)

def states(r): return {(x['source'],x['subject']):x['status'] for x in r['sources']}

def test_domain_search_runs_core_sources_and_explains_skips(world):
    r=run()
    assert {'dns.query','rdap.lookup','crtsh.lookup','urlscan.search','threatintel.otx_domain','history.wayback'}<=world.names()
    assert not {'history.commoncrawl','threatintel.virustotal_domain','threatintel.threatfox_search'}&world.names()
    st=states(r)
    assert st[('commoncrawl','—')]=='SKIPPED_MODE' and st[('virustotal','—')]=='SKIPPED_MISSING_SECRET' and st[('threatfox','—')]=='SKIPPED_MISSING_SECRET'
    assert any(e['source']=='rdap:created' for e in r['evidence']) and r['summary']['sources_ok']>=9

def test_package_contains_cti_exports_and_manifest(world):
    r=run(); z=zipfile.ZipFile(r['package_path']); names=set(z.namelist())
    assert {'report.html','case.json','stix.json','misp.json','manifest.json','evidence_ledger.csv','ioc_decisions.csv'}<=names
    assert {m['file'] for m in json.loads(z.read('manifest.json'))}>={'stix.json','misp.json','case.json'}

def test_safe_enrichment_adds_commoncrawl(world):
    run(mode='SAFE_ENRICHMENT'); assert 'history.commoncrawl' in world.names()

def test_keys_enable_virustotal_and_threatfox(world):
    r=run(secrets={'VT_API_KEY':'k','THREATFOX_AUTH_KEY':'k'})
    assert {'threatintel.virustotal_domain','threatintel.threatfox_search'}<=world.names()
    assert any(e['source']=='virustotal:malicious' and e['value']=='3' for e in r['evidence'])

@pytest.mark.parametrize('budget,expected',[('free',5),('balanced',12),('extended',20)])
def test_budget_limits_urlscan_detail_fetches(world,budget,expected):
    run(budget=budget); assert world.count('urlscan.result')==expected      # extended permite 30, mas só há 20 scans

def test_durable_identifiers_reach_the_ledger(world):
    r=run(); assert any(e['source']=='urlscan:durable_id' and e['value']=='google_analytics:UA-1234567-1' for e in r['evidence'])

def test_urlscan_details_stop_after_two_failures(world):
    def forbidden(*a,**k): raise urllib.error.HTTPError('http://x',403,'Forbidden',{},io.BytesIO(b''))
    world.set(urlscan,'result',forbidden)
    r=run(); assert world.count('urlscan.result')==2                       # circuit breaker: não insiste 12 vezes
    row=next(x for x in r['sources'] if x['source']=='urlscan:detalhes')
    assert row['status']=='UNAVAILABLE' and '403' in row['error'] and 'interrompida' in row['error']
    assert states(r)[('urlscan','novo-dominio.com')]=='OK'                 # a busca do urlscan em si deu certo

def test_ip_search_collects_ptr_rdap_and_hosted_domains(world):
    r=run('8.8.4.4')
    assert {'dns.reverse_ptr','rdap.lookup_ip','urlscan.search_ip'}<=world.names() and 'dns.query' not in world.names()
    srcs={e['source'] for e in r['evidence']}; assert {'dns:PTR','rdap_ip:org','rdap_ip:country','urlscan:hosted_domain'}<=srcs
    rels={(x['relationship'],x['to']) for x in r['relationships']}
    assert ('ptr','host.example.net') in rels and ('network_org','Org Exemplo') in rels and ('hosts_domain','a.example') in rels

def test_non_public_ips_are_not_queried(world):
    for ip in ('10.0.0.5','203.0.113.17','127.0.0.1'):        # privado, faixa de documentação, loopback
        world.calls.clear(); r=run(ip); assert not world.names() and states(r)[('coleta','—')]=='NOT_NEEDED'

def test_hash_needs_a_key_and_says_so(world):
    sha='d41d8cd98f00b204e9800998ecf8427e'
    r=run(sha); assert not world.names() and 'VT_API_KEY' in next(x for x in r['sources'] if x['source']=='coleta')['error']
    r=run(sha,secrets={'VT_API_KEY':'k'}); assert 'threatintel.virustotal_file' in world.names()
    assert any(e['source']=='virustotal:malicious' and e['value']=='9' for e in r['evidence'])

def test_email_collects_the_domain_phone_collects_nothing(world):
    run('alguem@novo-dominio.com'); assert 'dns.query' in world.names()
    world.calls.clear(); r=run('+55 11 99999-0000')
    assert not world.names() and 'privacidade' in next(x for x in r['sources'] if x['source']=='coleta')['error']

def test_lure_collects_malicious_domain_not_the_legit_platform(world):
    r=run(DEMO_LURE.replace('[.]example','[.]com'),case_id='LURE')
    queried={c[1] for c in world.calls if isinstance(c,tuple) and c[0]=='dns.query'}
    assert queried=={'receita-regulariza.com'} and r['summary']['input_type']=='LURE_TEXT'
    assert r['lures'][0]['brand']=='Receita Federal' and r['summary']['context_only']>=2
    assert all('wa.me' not in str(d['ioc']) for d in r['iocs'])           # plataforma legítima não vira decisão de bloqueio

def test_registration_batches_for_several_domains(world):
    r=run('a1-phish.com\na2-phish.com\nb-phish.net')
    assert len(r['batches'])==1 and set(r['batches'][0]['domains'])=={'a1-phish.com','a2-phish.com','b-phish.net'}

def test_similar_lures_via_memory_and_lure_text_not_exported(world,tmp_path):
    mem=str(tmp_path/'m.sqlite')
    first=run(DEMO_LURE,case_id='C-1',memory_enabled=True,memory_path=mem); assert first['similar_lures']==[]
    second=run(DEMO_LURE.replace('hoje','agora'),case_id='C-2',memory_enabled=True,memory_path=mem)
    assert [x['case_id'] for x in second['similar_lures']]==['C-1']
    case=json.loads(zipfile.ZipFile(second['package_path']).read('case.json')); assert 'lure_text' not in json.dumps(case)

def test_search_survives_every_source_failing(world):
    def down(*a,**k): raise urllib.error.URLError('sem rede')
    for mod,name in ((dns,'query'),(rdap,'lookup'),(crtsh,'lookup'),(urlscan,'search'),(threatintel,'otx_domain'),(history,'wayback')): world.set(mod,name,down)
    r=run(); s=r['summary']
    assert s['sources_ok']==0 and s['sources_failed']>=6 and r['report_path'] and 'falha de rede' in next(x for x in r['sources'] if x['status']=='UNAVAILABLE')['error']

def test_deadline_caps_a_hanging_source(world):
    def hang(*a,**k): time.sleep(3); return []
    world.set(history,'wayback',hang)
    t=time.time(); r=run(deadline=1.0)
    assert time.time()-t<2.6 and states(r)[('wayback','novo-dominio.com')]=='TIMEOUT' and states(r)[('rdap','novo-dominio.com')]=='OK'

def test_empty_target_is_rejected(world):
    with pytest.raises(ValueError): run('   ')

def test_progress_and_on_source_callbacks(world):
    msgs=[]; rows=[]
    run(progress=lambda frac,desc=None:msgs.append((round(frac,2),desc)),on_source=rows.append)
    assert msgs[0][0]<msgs[-1][0]==1.0 and any('Fontes' in (m[1] or '') for m in msgs) and len(rows)>=9

def test_rdap_dates_recorded_and_ioc_decisions_reflect_dns(world):
    r=run(); d=next(x for x in r['iocs'] if x['ioc']=='novo-dominio.com')
    assert d['ioc_type']=='domain' and d['decision'] in {'MONITOR','HUNT','INSUFFICIENT_EVIDENCE','DO_NOT_BLOCK'}
    assert any(e['source']=='rdap:expires' for e in r['evidence']) or any(e['source']=='rdap:created' for e in r['evidence'])

def test_workspace_env_is_honoured(world,tmp_path):
    r=run(); assert r['report_path'].startswith(str(tmp_path))

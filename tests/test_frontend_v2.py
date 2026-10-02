from tropeiro.frontend.demo import demo_result, DEMO_LURE
from tropeiro.frontend.app import render_outputs, _normalize_target
from tropeiro.frontend import views

def test_demo_is_offline_and_complete():
    r=demo_result()
    assert r['hybrid_entities'] and r['ai_edges'] and r['lures'][0]['brand']=='Receita Federal'
    assert {p.rsplit('/',1)[-1] for p in r['exports']}>={'stix.json','misp.json','sigma_dns.yml'}

def test_render_outputs_shape_and_escaping():
    out=render_outputs(demo_result())
    assert len(out)==16 and '<svg' in out[1] and 'Receita Federal' in out[3]
    assert 'Linha' not in out[9] and out[9].startswith('| Primeira')

def test_views_escape_html():
    bad=[{'from':'<script>alert(1)</script>','to':'x.example','relationship':'"><img>'}]
    svg=views.graph_svg(bad)
    assert '<script>' not in svg and '&lt;script&gt;' in svg
    assert '<img>' not in views.lure_html([{'brand':'<b>','theme':'t'}],[{'type':'domain','value':'<i>','methods':['rule'],'score':.9}])

def test_graph_empty_state():
    assert 'Sem relações' in views.graph_svg([])

def test_normalize_target_refangs_lure():
    kind,iocs=_normalize_target(DEMO_LURE,'LURE_TEXT')
    assert 'receita-regulariza.example' in iocs['domain']

def test_build_app_constructs():
    import pytest; pytest.importorskip('gradio')
    from tropeiro.frontend.app import build_app
    assert build_app() is not None

def test_ioc_rows_are_curated():
    r=demo_result(); rows=views.ioc_rows(r['iocs'])
    assert rows[0].keys()>={'IOC','decisão','risco de FP'} and {x['decisão'] for x in rows}>={'BLOCK','HUNT','MONITOR'}

def test_run_quick_case_lure_with_sources_down(monkeypatch,tmp_path):
    import urllib.error
    from tropeiro import http
    from tropeiro.frontend import app as fe
    def down(*a,**k): raise urllib.error.URLError('offline')
    monkeypatch.setattr(http,'request',down)
    monkeypatch.setattr(fe.tempfile,'gettempdir',lambda:str(tmp_path))
    res=fe.run_quick_case(DEMO_LURE,'LURE_TEXT',case_id='T-1',memory_enabled=False)
    assert res['lures'][0]['brand']=='Receita Federal'
    assert any(e['type']=='cpf' or e['type']=='whatsapp' for e in res['hybrid_entities'])
    assert res['summary']['sources_failed']>0 and res['summary']['ai'].endswith('extração: regras')
    assert {p.rsplit('/',1)[-1] for p in res['exports']}>={'stix.json','misp.json'}
    assert len(render_outputs(res))==16

def test_workbench_records_rdap_dates_in_ledger(monkeypatch,tmp_path):
    from tropeiro.frontend import app as fe
    monkeypatch.setattr(fe.tempfile,'gettempdir',lambda:str(tmp_path))
    monkeypatch.setattr(fe.dns,'query',lambda *a,**k:[])
    monkeypatch.setattr(fe.crtsh,'lookup',lambda *a,**k:[])
    monkeypatch.setattr(fe.urlscan,'search',lambda *a,**k:{})
    monkeypatch.setattr(fe.threatintel,'otx_domain',lambda *a,**k:{})
    monkeypatch.setattr(fe.rdap,'lookup',lambda d:{'created':'2026-09-20T10:00:00Z','expires':'2027-09-20T10:00:00Z','registrar_orgs':['R'],'registrant_orgs':[]})
    res=fe.run_quick_case('novo-dominio.example','DOMAIN',case_id='RDAP-1',memory_enabled=False)
    srcs={(e['source'],e['value']) for e in res['evidence']}
    assert ('rdap:created','2026-09-20T10:00:00Z') in srcs and ('rdap:expires','2027-09-20T10:00:00Z') in srcs

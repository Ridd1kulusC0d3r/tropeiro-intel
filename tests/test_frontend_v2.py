from tropeiro.frontend.demo import demo_result, DEMO_LURE
from tropeiro.frontend.app import render_outputs, _normalize_target
from tropeiro.frontend import views

def test_demo_is_offline_and_complete():
    r=demo_result()
    assert r['hybrid_entities'] and r['ai_edges'] and r['lures'][0]['brand']=='Receita Federal'
    assert {p.rsplit('/',1)[-1] for p in r['exports']}>={'stix.json','misp.json','sigma_dns.yml'}

def test_render_outputs_shape_and_escaping():
    out=render_outputs(demo_result())
    assert len(out)==18 and '<svg' in out[1] and 'Receita Federal' in out[3]
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



def test_demo_has_campaign_signals():
    r=demo_result()
    assert len(r['batches'])==1 and len(r['batches'][0]['domains'])==2 and r['similar_lures'][0]['similarity']>0.8


def test_run_quick_case_survives_every_source_failing(monkeypatch,tmp_path):
    """O conftest bloqueia a rede: todas as fontes falham, e a busca ainda entrega relatório e extração da isca."""
    from tropeiro.frontend.app import N_OUTPUTS
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path)); monkeypatch.setenv('HOME',str(tmp_path))
    from tropeiro.frontend import app as fe
    res=fe.run_quick_case(DEMO_LURE.replace('[.]example','[.]com'),'LURE_TEXT',case_id='T-1',memory_enabled=False,use_cache=False)
    s=res['summary']
    assert res['lures'][0]['brand']=='Receita Federal' and s['sources_ok']==0 and s['sources_failed']>0 and s['ai'].endswith('extração: regras')
    assert any(x['type']=='whatsapp' for x in res['hybrid_entities']) and len(render_outputs(res))==N_OUTPUTS

def test_stream_investigation_shows_progress_then_results(monkeypatch,tmp_path):
    from tropeiro.frontend.app import stream_investigation, N_OUTPUTS
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path)); monkeypatch.setenv('HOME',str(tmp_path))
    steps=list(stream_investigation('+55 11 99999-0000','AUTO','S-1','a','','','PASSIVE','balanced','OFF',False,'',noop=[None]*(N_OUTPUTS-1)))
    assert all(len(x)==N_OUTPUTS for x in steps) and 'COLETANDO' in steps[0][0] and 'INVESTIGAÇÃO CONCLUÍDA' in steps[-1][0]

def test_stream_investigation_turns_errors_into_a_panel(monkeypatch):
    from tropeiro.frontend import app as fe2
    monkeypatch.setattr(fe2,'investigate',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('quebrou de propósito')))
    steps=list(fe2.stream_investigation('example.com','AUTO','E-1','a','','','PASSIVE','balanced','OFF',False,'',noop=[None]*(fe2.N_OUTPUTS-1)))
    assert 'NÃO CONCLUIU' in steps[-1][0] and 'quebrou de propósito' in steps[-1][0] and 'tropeiro doctor' in steps[-1][0]

def test_stream_investigation_rejects_empty_input():
    from tropeiro.frontend.app import stream_investigation, N_OUTPUTS
    out=list(stream_investigation('  ','AUTO','x','a','','','PASSIVE','balanced','OFF',False,'',noop=[None]*(N_OUTPUTS-1)))
    assert len(out)==1 and 'Informe' in out[0][0]

def test_publish_files_copies_outputs_to_a_servable_dir(tmp_path,monkeypatch):
    """Regressão: o Gradio recusa arquivos fora da pasta temporária/atual (InvalidPathError) e a tela ficava sem resultado."""
    import tempfile
    from pathlib import Path
    from tropeiro.frontend.app import publish_files
    workdir=tmp_path/'custom_workspace'; workdir.mkdir()
    for n in ('report.html','pack.zip','stix.json'): (workdir/n).write_text(n)
    monkeypatch.setattr(tempfile,'gettempdir',lambda:str(tmp_path/'systmp'))
    out=publish_files({'summary':{'case_id':'P-1'},'exports':[str(workdir/'stix.json')],'report_path':str(workdir/'report.html'),'package_path':str(workdir/'pack.zip')})
    for key in ('report_path','package_path'): assert str(tmp_path/'systmp') in out[key] and Path(out[key]).read_text()
    assert str(tmp_path/'systmp') in out['exports'][0] and (workdir/'stix.json').exists()      # original intacto

def test_launch_allows_the_workspace_dir(monkeypatch,tmp_path):
    from tropeiro.frontend import app as fe2
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path/'ws'))
    assert str(tmp_path/'ws') in fe2._allowed()

def test_colab_launch_lets_gradio_decide_sharing(monkeypatch):
    """Regressão: com share=False explícito o Workbench não aparecia no Colab (o Gradio só liga share sozinho se for None)."""
    from tropeiro.frontend import app as fe3
    seen={}
    class FakeApp:
        launch_style={}
        def queue(self): return self
        def launch(self,**kw): seen.update(kw)
    monkeypatch.setattr(fe3,'build_app',lambda:FakeApp())
    fe3.launch_colab_frontend(7860,True)
    assert seen['share'] is None and seen['inline'] is True and seen['prevent_thread_lock'] is True and seen['allowed_paths']

def test_launch_local_uses_a_free_port_and_loopback(monkeypatch):
    from tropeiro.frontend import app as fe3
    seen={}
    class FakeApp:
        launch_style={}
        def queue(self): return self
        def launch(self,**kw): seen.update(kw)
    monkeypatch.setattr(fe3,'build_app',lambda:FakeApp())
    fe3.launch_local(None,False,open_browser=False)
    assert seen['server_name']=='127.0.0.1' and 7860<=seen['server_port']<7900 and seen['inbrowser'] is False and seen['share'] is False

def test_free_port_skips_busy_ports():
    import socket
    from tropeiro.frontend.app import _free_port
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); busy=s.getsockname()[1]; s.listen(1)
        assert _free_port(busy,5)!=busy

import io, json, urllib.error
import pytest
from tropeiro import doctor
from tropeiro.cli import main
from tropeiro.collectors import crtsh, dns, history, rdap, threatintel, urlscan

def test_offline_checks_pass_in_a_working_environment(monkeypatch,tmp_path):
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path)); monkeypatch.setenv('HOME',str(tmp_path))
    checks=doctor.run_checks(network=False); names={c.name for c in checks}
    assert {'Python','dependência: tldextract','dependência: stix2','pasta de trabalho','chaves de API (opcionais)'}<=names
    assert doctor.verdict(checks) in {'OK','DEGRADADO'} and 'Resultado' in doctor.format_text(checks)

def test_network_probe_distinguishes_essential_from_optional(monkeypatch):
    def fake(req,timeout=0):
        if 'cloudflare' in req.full_url or 'rdap' in req.full_url: raise urllib.error.URLError('sem rede')
        raise urllib.error.HTTPError(req.full_url,403,'no',{},io.BytesIO(b''))
    monkeypatch.setattr(doctor.urllib.request,'urlopen',fake)
    checks=doctor.check_network(timeout=1)
    by={c.name:c for c in checks}
    assert by['rede: DNS-over-HTTPS (cloudflare-dns.com)'].status=='FAIL' and 'essencial' in by['rede: DNS-over-HTTPS (cloudflare-dns.com)'].hint
    assert by['rede: urlscan.io'].status=='OK'                       # respondeu 403: a rede chega, a fonte é que recusou
    assert doctor.verdict(checks)=='FALHA'

def test_optional_source_down_only_degrades(monkeypatch):
    class R:
        status=200
        def __enter__(s): return s
        def __exit__(s,*a): return False
        def read(s,n=0): return b'{}'
    def fake(req,timeout=0):
        if 'archive.org' in req.full_url: raise urllib.error.URLError('reset')
        return R()
    monkeypatch.setattr(doctor.urllib.request,'urlopen',fake)
    checks=doctor.check_network(timeout=1); assert doctor.verdict(checks)=='DEGRADADO'
    assert next(c for c in checks if 'Wayback' in c.name).status=='WARN'

def test_cli_doctor_offline_exit_code(monkeypatch,tmp_path,capsys):
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path)); monkeypatch.setenv('HOME',str(tmp_path))
    assert main(['doctor','--offline'])==0 and 'Resultado' in capsys.readouterr().out

@pytest.fixture
def fake_sources(monkeypatch,tmp_path):
    monkeypatch.setenv('TROPEIRO_WORKSPACE',str(tmp_path)); monkeypatch.setenv('HOME',str(tmp_path))
    for k in ('VT_API_KEY','THREATFOX_AUTH_KEY','URLSCAN_API_KEY'): monkeypatch.delenv(k,raising=False)
    monkeypatch.setattr(dns,'query',lambda d,t='A':['203.0.113.9'] if t=='A' else [])
    monkeypatch.setattr(rdap,'lookup',lambda d:{'created':'2026-09-01T00:00:00Z','registrar_orgs':['R'],'registrant_orgs':[],'nameservers':[]})
    monkeypatch.setattr(crtsh,'lookup',lambda d:[]); monkeypatch.setattr(urlscan,'search',lambda d,k='':{}); monkeypatch.setattr(threatintel,'otx_domain',lambda d:{})
    monkeypatch.setattr(history,'wayback',lambda d,n=0:[])

def test_cli_search_prints_progress_summary_and_files(fake_sources,capsys):
    code=main(['search','novo-dominio.com','--no-memory','--no-cache','--case','CLI-1'])
    out,err=capsys.readouterr()
    assert code==0 and 'consultas em paralelo' in err and '✓ dns:A' in err and 'SKIPPED_MISSING_SECRET' in err
    assert 'novo-dominio.com' in out and 'Relatório:' in out and 'Pacote:' in out and 'evidências' in out

def test_cli_search_json_and_quiet(fake_sources,capsys):
    assert main(['search','novo-dominio.com','--no-memory','--no-cache','--json','-q'])==0
    out,err=capsys.readouterr(); data=json.loads(out)
    assert err=='' and data['summary']['input_type']=='DOMAIN' and data['summary']['sources_ok']>=5 and data['report'].endswith('.html')

def test_cli_search_reads_text_from_a_file(fake_sources,tmp_path,capsys):
    f=tmp_path/'isca.txt'; f.write_text('Receita Federal: acesse hxxps://receita-fake[.]com/cpf agora',encoding='utf-8')
    assert main(['search',str(f),'--no-memory','--no-cache'])==0
    out,err=capsys.readouterr(); assert 'LURE_TEXT' in err and 'Receita Federal' in out

def test_cli_search_exit_2_when_no_source_answers(fake_sources,monkeypatch,capsys):
    def down(*a,**k): raise urllib.error.URLError('sem rede')
    for mod,name in ((dns,'query'),(rdap,'lookup'),(crtsh,'lookup'),(urlscan,'search'),(threatintel,'otx_domain'),(history,'wayback')): monkeypatch.setattr(mod,name,down)
    assert main(['search','novo-dominio.com','--no-memory','--no-cache'])==2
    assert 'tropeiro doctor' in capsys.readouterr().err

def test_cli_search_phone_explains_why_nothing_is_queried(fake_sources,capsys):
    assert main(['search','+55 11 99999-0000','--no-memory','--no-cache'])==0
    assert 'privacidade' in capsys.readouterr().err

def test_cli_workbench_parser_defaults():
    from tropeiro.cli import build_parser
    a=build_parser().parse_args(['workbench']); assert a.port is None and not a.share and not a.no_browser

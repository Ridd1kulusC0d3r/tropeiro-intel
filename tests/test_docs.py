"""A documentação é parte do produto: exemplos executam e links não quebram."""
import re, os
from pathlib import Path
import pytest

@pytest.fixture(autouse=True)
def _restore_http_state():
    from tropeiro import http
    interval,cache=http.MIN_INTERVAL,http._cache
    yield
    http.MIN_INTERVAL,http._cache=interval,cache

ROOT=Path(__file__).resolve().parents[1]
DOCS=sorted((ROOT/'docs').glob('*.md'))
MD=DOCS+[ROOT/'README.md',ROOT/'CONTRIBUTING.md']

def _blocks(path):
    return re.findall(r"```python\n(.*?)```",path.read_text(encoding='utf-8'),flags=re.S)

@pytest.mark.parametrize('path',[p for p in DOCS if _blocks(p)],ids=lambda p:p.name)
def test_python_examples_run_offline(path,monkeypatch):
    monkeypatch.chdir(ROOT)
    for i,code in enumerate(_blocks(path)):
        exec(compile(code,f'{path.name}#{i}','exec'),{})

@pytest.mark.parametrize('path',MD,ids=lambda p:str(p.relative_to(ROOT)))
def test_relative_links_exist(path):
    text=re.sub(r"```.*?```","",path.read_text(encoding='utf-8'),flags=re.S)
    missing=[]
    for target in re.findall(r"\]\(([^)\s]+)\)",text):
        if target.startswith(('http://','https://','mailto:','#')): continue
        file=target.split('#')[0]
        if file and not (path.parent/file).resolve().exists(): missing.append(target)
    assert not missing,f'links quebrados em {path.name}: {missing}'

def test_anchors_point_to_existing_headings():
    def slug(h): return re.sub(r'[^\w\- ]','',h.strip().lower()).replace(' ','-')
    bad=[]
    for path in MD:
        text=path.read_text(encoding='utf-8'); body=re.sub(r"```.*?```","",text,flags=re.S)
        for target in re.findall(r"\]\(([^)\s]+\.md)#([^)\s]+)\)",body)+[(path.name,a) for a in re.findall(r"\]\(#([^)\s]+)\)",body)]:
            file,anchor=target; dest=(path.parent/file).resolve()
            if not dest.exists(): continue
            heads={slug(h) for h in re.findall(r"^#{1,6}\s+(.+)$",re.sub(r"```.*?```","",dest.read_text(encoding='utf-8'),flags=re.S),flags=re.M)}
            if anchor not in heads: bad.append(f'{path.name} -> {file}#{anchor}')
    assert not bad,bad

def test_docs_index_lists_every_doc():
    index=(ROOT/'docs'/'README.md').read_text(encoding='utf-8')
    missing=[p.name for p in DOCS if p.name!='README.md' and p.name not in index]
    assert not missing,f'docs fora do índice: {missing}'

def test_documented_cli_example_matches_real_output(capsys,tmp_path):
    from tropeiro.cli import main
    assert main(['lure',str(ROOT/'examples'/'lure_receita.txt'),'--case','CASO-001','--out',str(tmp_path)])==0
    out=capsys.readouterr().out
    cli=(ROOT/'docs'/'CLI.md').read_text(encoding='utf-8')
    for fragment in ('"brand": "Receita Federal"','"receita-regulariza.example"','"somente_contexto"','defanged: receita-regulariza[.]example'):
        assert fragment in cli, f'a doc CLI.md não mostra {fragment}'
    for fragment in ('"brand": "Receita Federal"','"receita-regulariza.example"','"somente_contexto"','defanged: receita-regulariza[.]example'):
        assert fragment in out

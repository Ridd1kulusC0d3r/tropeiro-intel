"""Diagnóstico do ambiente: `tropeiro doctor` e o painel "Diagnóstico" do Workbench.

Responde, sem rodar uma investigação: o Python e as dependências servem? as pastas são graváveis? a rede alcança cada fonte?
"""
from __future__ import annotations
import importlib, os, platform, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List

OK, WARN, FAIL = "OK", "WARN", "FAIL"

@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    hint: str = ""

CORE_DEPS = ("tldextract", "rapidfuzz", "pandas", "networkx", "stix2")
UI_DEPS = ("gradio",)
AI_DEPS = ("gliner", "transformers", "torch", "sentencepiece", "google.protobuf")

# (nome, url, essencial). "Essencial": sem DNS-over-HTTPS e RDAP quase nenhuma busca funciona.
NETWORK_SOURCES = [
    ("DNS-over-HTTPS (cloudflare-dns.com)", "https://cloudflare-dns.com/dns-query?name=example.com&type=A", True, {"accept": "application/dns-json"}),
    ("RDAP (rdap.org)", "https://rdap.org/domain/example.com", True, {}),
    ("crt.sh", "https://crt.sh/?q=example.com&output=json&exclude=expired", False, {}),
    ("urlscan.io", "https://urlscan.io/api/v1/search/?q=domain:example.com&size=1", False, {}),
    ("Wayback Machine", "https://web.archive.org/cdx/search/cdx?url=example.com&limit=1&output=json", False, {}),
    ("AlienVault OTX", "https://otx.alienvault.com/api/v1/indicators/domain/example.com/general", False, {}),
]

def _version(mod: str) -> str:
    try:
        m = importlib.import_module(mod)
        return str(getattr(m, "__version__", "instalado"))
    except Exception:
        return ""

def check_python() -> Check:
    v = sys.version_info
    ok = v >= (3, 10)
    return Check("Python", OK if ok else FAIL, f"{platform.python_version()} ({platform.system()})",
                 "" if ok else "o Tropeiro exige Python 3.10 ou mais novo")

def check_deps() -> List[Check]:
    out = []
    for mod in CORE_DEPS:
        v = _version(mod)
        out.append(Check(f"dependência: {mod}", OK if v else FAIL, v, "" if v else 'pip install -e "."'))
    g = _version("gradio")
    if not g:
        out.append(Check("Workbench (gradio)", WARN, "não instalado", 'pip install -e ".[colab]"  (só necessário para a interface; a CLI funciona sem)'))
    else:
        major = int(g.split(".")[0]) if g[0].isdigit() else 0
        out.append(Check("Workbench (gradio)", OK if 4 <= major < 7 else WARN, g, "" if 4 <= major < 7 else "versão fora da faixa testada (>=4.44,<7)"))
    ai = {m: _version(m) for m in AI_DEPS}
    missing = [m for m, v in ai.items() if not v]
    out.append(Check("IA opcional (GLiNER/Qwen)", OK if not missing else WARN,
                     "completa" if not missing else "faltam: " + ", ".join(missing),
                     "" if not missing else 'pip install -e ".[ai]"  (opcional: sem IA as regras brasileiras continuam funcionando)'))
    return out

def check_dirs() -> List[Check]:
    from .pipeline import default_base
    out = []
    for label, path in (("pasta de trabalho", default_base()), ("pasta ~/.tropeiro (cache e memória)", Path.home() / ".tropeiro")):
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".tropeiro_probe"; probe.write_text("ok"); probe.unlink()
            out.append(Check(label, OK, str(path)))
        except Exception as exc:
            out.append(Check(label, FAIL, f"{path}: {exc}", "defina TROPEIRO_MEMORY_PATH ou ajuste as permissões da pasta"))
    return out

def check_proxy() -> Check:
    found = {k: v for k, v in os.environ.items() if k.lower() in ("https_proxy", "http_proxy", "all_proxy") and v}
    return Check("proxy", OK, ", ".join(sorted(found)) if found else "nenhum", "se a rede falhar, confira se o proxy permite estes domínios" if found else "")

def _probe(item, timeout: float):
    name, url, essential, headers = item
    t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TropeiroIntel/doctor", **headers})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(256)
            code = r.status
        return Check(f"rede: {name}", OK, f"HTTP {code} em {time.time()-t:.1f}s")
    except urllib.error.HTTPError as exc:      # a fonte respondeu: a rede chega nela
        return Check(f"rede: {name}", OK if exc.code in (403, 429) else WARN, f"HTTP {exc.code} em {time.time()-t:.1f}s",
                     "a fonte respondeu mas recusou (pode exigir chave ou ter limite de uso)")
    except Exception as exc:
        return Check(f"rede: {name}", FAIL if essential else WARN, f"{type(exc).__name__}: {str(exc)[:110]}",
                     "fonte essencial inalcançável: verifique internet/proxy" if essential else
                     "fonte opcional inalcançável: a busca segue sem ela (status UNAVAILABLE)")

def check_network(timeout: float = 12.0) -> List[Check]:
    with ThreadPoolExecutor(max_workers=len(NETWORK_SOURCES)) as pool:
        return list(pool.map(lambda it: _probe(it, timeout), NETWORK_SOURCES))

def check_keys() -> Check:
    from .config import SECRET_NAMES, secret
    have = [k for k in SECRET_NAMES if secret(k)]
    return Check("chaves de API (opcionais)", OK, ", ".join(have) if have else "nenhuma (o núcleo funciona sem)")

def run_checks(network: bool = True, timeout: float = 12.0) -> List[Check]:
    checks = [check_python(), *check_deps(), *check_dirs(), check_proxy(), check_keys()]
    if network:
        checks += check_network(timeout)
    return checks

def verdict(checks: List[Check]) -> str:
    """'OK', 'DEGRADADO' (algo opcional falhou) ou 'FALHA' (a busca não vai funcionar)."""
    if any(c.status == FAIL for c in checks): return "FALHA"
    return "DEGRADADO" if any(c.status == WARN for c in checks) else "OK"

def format_text(checks: List[Check]) -> str:
    icon = {OK: "✓", WARN: "⚠", FAIL: "✗"}
    lines = []
    for c in checks:
        lines.append(f"{icon[c.status]} {c.name:42s} {c.detail}")
        if c.hint and c.status != OK:
            lines.append(f"    → {c.hint}")
    lines.append(f"\nResultado: {verdict(checks)}")
    return "\n".join(lines)

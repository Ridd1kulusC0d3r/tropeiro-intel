"""CLI do Tropeiro: `search` (busca completa), `doctor` (diagnóstico), `lure` (isca offline) e `workbench` (interface)."""
import argparse, json, sys
from pathlib import Path
from . import __version__
from .intelligence.br_lures import detect_br_lures, extract_lure_infra
from .intelligence.legit_domains import partition_iocs
from .intelligence.sigma import sigma_rules
from .reporting.misp import misp_event
from .reporting.stix import bundle_from_iocs
from .utils import defang

ICON = {"OK": "✓", "UNAVAILABLE": "✗", "TIMEOUT": "⏱"}

def _read_target(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg)
    try:
        if len(arg) < 260 and p.is_file():
            return p.read_text(encoding="utf-8")
    except OSError:
        pass
    return arg

def cmd_lure(a) -> int:
    text = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    iocs = extract_lure_infra(text)
    act, ctx = partition_iocs(iocs)
    print(json.dumps({"lures": detect_br_lures(text), "iocs": iocs, "somente_contexto": ctx}, ensure_ascii=False, indent=2))
    print("defanged:", ", ".join(defang(d) for d in act.get("domain", [])) or "-")
    if a.out:
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / "stix.json").write_text(bundle_from_iocs(act, case_id=a.case, tlp=a.tlp, context_only=ctx).serialize(pretty=True), encoding="utf-8")
        (out / "misp.json").write_text(json.dumps(misp_event(a.case, act, tlp=a.tlp, context_only=ctx), ensure_ascii=False, indent=2), encoding="utf-8")
        for k, v in sigma_rules(act, a.case).items():
            (out / f"sigma_{k}.yml").write_text(v + "\n", encoding="utf-8")
        print("exportado em", out)
    return 0

def cmd_search(a) -> int:
    from .pipeline import investigate, plan_investigation
    from .targets import parse_target
    from .config import secret, SECRET_NAMES
    from .sources import BUDGET_DEADLINE
    text = _read_target(a.target)
    tgt = parse_target(text, a.type)
    secrets = {k: secret(k) for k in SECRET_NAMES}
    _ctx, tasks, skipped = plan_investigation(tgt, a.mode, a.budget, secrets)
    deadline = a.deadline or BUDGET_DEADLINE.get(a.budget, 90.0)
    say = (lambda *x: None) if a.quiet else (lambda *x: print(*x, file=sys.stderr, flush=True))
    say(f"Tropeiro Intel {__version__} · caso {a.case}")
    label = tgt.text.replace("\n", " ")[:70] + ("…" if len(tgt.text) > 70 else "")
    say(f"Alvo: {label}  [{tgt.kind}]  modo {a.mode} · profundidade {a.budget} · prazo {deadline:.0f}s")
    if tgt.domains or tgt.ips or tgt.hashes:
        say(f"Assuntos: {len(tgt.domains)} domínio(s), {len(tgt.ips)} IP(s), {len(tgt.hashes)} hash(es) → {len(tasks)} consultas em paralelo")
    for s in tgt.skipped_legit:
        say(f"  · {s}: plataforma legítima ou IP não público (contexto, não coletado)")

    def on_source(row):
        extra = f" — {row['error']}" if row["error"] else (f"  {row['items']} itens" if row["items"] else "")
        say(f"  {ICON.get(row['status'], '·')} {row['source']:<18s} {row['subject']:<28s} {row['seconds']:5.1f}s{extra}")

    try:
        r = investigate(text, a.type, case_id=a.case, analyst=a.analyst, brand=a.brand, mode=a.mode, budget=a.budget,
                        ai_mode=a.ai, memory_enabled=not a.no_memory, memory_path=a.memory_path or "",
                        workspace=Path(a.workspace) if a.workspace else None, deadline=a.deadline, use_cache=not a.no_cache,
                        on_source=on_source)
    except Exception as exc:
        print(f"Erro: {type(exc).__name__}: {exc}\nRode `tropeiro doctor` para diagnosticar o ambiente.", file=sys.stderr)
        return 1
    s = r["summary"]
    for row in skipped:
        say(f"  – {row['source']:<18s} {row['status']}: {row['error']}")
    if a.json:
        print(json.dumps({"summary": s, "iocs": r["iocs"], "sources": r["sources"], "report": r["report_path"], "package": r["package_path"]},
                         ensure_ascii=False, indent=2, default=str))
    else:
        print(f"\nConcluído em {s['elapsed_s']}s · {s['evidence']} evidências · {s['sources_ok']} fontes OK · "
              f"{s['sources_failed']} indisponíveis · {s['sources_skipped']} puladas")
        if r["iocs"]:
            print(f"\n{'IOC':<44s} {'tipo':<8s} {'decisão':<20s} {'confiança':<13s} risco FP")
            for d in r["iocs"][:25]:
                print(f"{str(d['ioc'])[:43]:<44s} {d['ioc_type']:<8s} {d['decision']:<20s} {d['confidence_band']:<13s} {d['false_positive_risk']}")
        if r["lures"]:
            print("\nIsca:", "; ".join(f"{x['brand']} · {x['theme']}" for x in r["lures"]))
        print(f"\nRelatório: {r['report_path']}\nPacote:    {r['package_path']}")
    if tasks and s["sources_ok"] == 0:
        print("\nNenhuma fonte respondeu: provável problema de rede/proxy. Rode `tropeiro doctor`.", file=sys.stderr)
        return 2
    return 0

def cmd_doctor(a) -> int:
    from .doctor import run_checks, format_text, verdict
    checks = run_checks(network=not a.offline, timeout=a.timeout)
    print(f"Tropeiro Intel {__version__} · diagnóstico\n")
    print(format_text(checks))
    return 1 if verdict(checks) == "FALHA" else 0

def cmd_workbench(a) -> int:
    from .frontend.app import launch_local
    launch_local(a.port, a.share, open_browser=not a.no_browser)
    return 0

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="tropeiro", description=f"Tropeiro Intel {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="busca completa (coleta, decisão, relatório) sem interface")
    s.add_argument("target", help="domínio, URL, IP, e-mail, hash, telefone, texto da isca, arquivo de texto ou '-' (entrada padrão)")
    s.add_argument("--type", default="AUTO", choices=["AUTO", "DOMAIN", "URL", "IP", "EMAIL", "HASH", "PHONE", "MULTI_IOC", "LURE_TEXT"])
    s.add_argument("--mode", default="PASSIVE", choices=["PASSIVE", "SAFE_ENRICHMENT", "AUTHORIZED_ACTIVE"])
    s.add_argument("--budget", default="balanced", choices=["free", "balanced", "extended"])
    s.add_argument("--case", default="TI-CLI-001"); s.add_argument("--analyst", default="Analista"); s.add_argument("--brand", default="")
    s.add_argument("--ai", default="OFF", choices=["OFF", "GLINER_ONLY", "GLINER_QWEN", "AUTO"])
    s.add_argument("--no-memory", action="store_true"); s.add_argument("--memory-path"); s.add_argument("--workspace")
    s.add_argument("--deadline", type=float, help="prazo total da coleta em segundos (padrão: 45/90/180 conforme a profundidade)")
    s.add_argument("--no-cache", action="store_true"); s.add_argument("--json", action="store_true"); s.add_argument("-q", "--quiet", action="store_true")
    s.set_defaults(fn=cmd_search)

    d = sub.add_parser("doctor", help="diagnostica Python, dependências, pastas e a rede até cada fonte")
    d.add_argument("--offline", action="store_true", help="não testa a rede"); d.add_argument("--timeout", type=float, default=12.0)
    d.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("lure", help="analisa texto de isca offline: marca/tema, IOCs, PIX/WhatsApp, e exporta STIX/MISP/Sigma")
    p.add_argument("file", help="arquivo de texto ('-' = entrada padrão)")
    p.add_argument("--case", default="CASE"); p.add_argument("--tlp", default="AMBER")
    p.add_argument("--out", help="diretório para stix.json, misp.json e sigma_*.yml")
    p.set_defaults(fn=cmd_lure)

    w = sub.add_parser("workbench", help="abre o Workbench (interface web) no navegador local")
    w.add_argument("--port", type=int, default=None, help="porta (padrão: a primeira livre a partir de 7860)")
    w.add_argument("--share", action="store_true", help="link público temporário do Gradio (cuidado com dados do caso)")
    w.add_argument("--no-browser", action="store_true", help="não abre o navegador")
    w.set_defaults(fn=cmd_workbench)
    return ap

def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a)

if __name__ == "__main__":
    sys.exit(main())

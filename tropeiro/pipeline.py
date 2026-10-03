"""Pipeline único de investigação: alvo -> plano de fontes -> coleta concorrente -> decisão -> relatório/exportações.

Usado pelo Workbench, pela CLI (`tropeiro search`) e pela API Python (`investigate`). Nada aqui depende de Gradio.
"""
from __future__ import annotations

import json, re, tempfile, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import __version__, enrichment, http
from .collectors import crtsh, dns, history, rdap, threatintel, urlscan
from .config import Settings, secret, SECRET_NAMES
from .correlation.registration import registration_batches
from .evidence.ledger import build as build_ledger
from .intelligence.br_lures import detect_br_lures
from .intelligence.decision_objects import build_ioc_decisions
from .intelligence.legit_domains import partition_iocs
from .intelligence.sigma import sigma_rules
from .intelligence.warninglists import WarningListEngine
from .memory import CaseMemory, default_memory_path
from .models import Observation
from .onboarding import budget_limits, features_for_target, skip_reason, SOURCE_FLAGS
from .reporting.context import build_report_data
from .reporting.exporter import export_selected, write_manifest, zip_exports
from .reporting.misp import misp_event
from .reporting.rich_html import build_report
from .reporting.stix import bundle_from_iocs
from .sources import BUDGET_DEADLINE, Task, describe_error, run_tasks, skipped_row, status_row
from .targets import Target, parse_target
from .timeline import build_timeline, timeline_markdown

Progress = Optional[Callable[[float, str], None]]
DOMAIN_ONLY_NOTE = "nenhuma fonte pública é consultada para este tipo, por privacidade; o valor entra no caso para correlação e memória"


# --- contexto de coleta ------------------------------------------------------------------------------------------

@dataclass
class Ctx:
    target: Target
    secrets: Dict[str, str]
    feats: Dict[str, bool]
    limits: Dict[str, int]
    ownership: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    rdap_rows: List[Dict[str, Any]] = field(default_factory=list)


def relationship_rows(ownership: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Relações (de, tipo, para, fonte) a partir do que foi coletado, para o grafo e a tabela de relações."""
    rows = []
    for subject, data in (ownership or {}).items():
        for rtype, values in (data.get("dns") or {}).items():
            for value in values or []:
                rows.append({"from": subject, "relationship": f"dns_{rtype.lower()}", "to": value, "source": f"dns:{rtype}"})
        for org in (data.get("rdap") or {}).get("registrant_orgs", []) or []:
            rows.append({"from": subject, "relationship": "registrant_org", "to": org, "source": "rdap"})
        for name in (data.get("cert_names") or [])[:100]:
            if name and name != subject:
                rows.append({"from": subject, "relationship": "certificate_name", "to": name, "source": "crt.sh"})
        for name in data.get("ptr") or []:
            rows.append({"from": subject, "relationship": "ptr", "to": name, "source": "dns:PTR"})
        ip = data.get("rdap_ip") or {}
        for org in ip.get("orgs", []) or []:
            rows.append({"from": subject, "relationship": "network_org", "to": org, "source": "rdap_ip"})
        for dom in data.get("hosted_domains") or []:
            rows.append({"from": subject, "relationship": "hosts_domain", "to": dom, "source": "urlscan"})
    return rows


# --- tarefas de coleta (uma por fonte e assunto) ---------------------------------------------------------------------

def _o(entity, etype, source, value, notes=""):
    return Observation(str(entity), etype, source, str(value), notes=notes)


def _domain_tasks(ctx: Ctx, d: str) -> List[Task]:
    f, S, tasks = ctx.feats, ctx.secrets, []
    own = ctx.ownership.setdefault(d, {"domain": d, "dns": {}, "rdap": {}, "cert_names": []})

    if f["ENABLE_DNS"]:
        for rtype in ("A", "AAAA", "CNAME", "MX", "NS"):
            def dns_fn(rtype=rtype):
                values = dns.query(d, rtype) or []
                own["dns"][rtype] = values
                return [_o(d, "domain", f"dns:{rtype}", v) for v in values]
            tasks.append(Task(f"dns:{rtype}", d, dns_fn))

    if f["ENABLE_RDAP"]:
        def rdap_fn():
            r = rdap.lookup(d) or {}
            own["rdap"] = r
            out = [_o(d, "domain", "rdap:registrant_org", x) for x in r.get("registrant_orgs", []) or []]
            out += [_o(d, "domain", "rdap:registrar_org", x) for x in r.get("registrar_orgs", []) or []]
            out += [_o(d, "domain", f"rdap:{k}", r[k]) for k in ("created", "updated", "expires") if r.get(k)]
            if r.get("created"):
                ctx.rdap_rows.append({"domain": d, "created": r["created"], "registrar": "; ".join(r.get("registrar_orgs") or []),
                                      "nameservers": r.get("nameservers") or []})
            return out
        tasks.append(Task("rdap", d, rdap_fn))

    if f["ENABLE_CT"]:
        def ct_fn():
            ct = crtsh.lookup(d) or []
            names = set()
            for row in ct if isinstance(ct, list) else []:
                for name in str(row.get("name_value", "")).splitlines():
                    name = name.strip().lower().lstrip("*.")
                    if name:
                        names.add(name)
            own["cert_names"] = sorted(names)[:500]
            return [_o(d, "domain", "crt.sh", n) for n in own["cert_names"]]
        tasks.append(Task("crt.sh", d, ct_fn))

    if f["ENABLE_URLSCAN"]:
        def urlscan_fn():
            u = urlscan.search(d, S.get("URLSCAN_API_KEY", "")) or {}
            results = u.get("results", []) if isinstance(u, dict) else []
            out = []
            for row in results[:100]:
                value = (row.get("page") or {}).get("url") or (row.get("task") or {}).get("url")
                if value:
                    out.append(_o(d, "domain", "urlscan", value))
            extra = []
            if f["ENABLE_URLSCAN_DETAILS"]:
                ids = [x["_id"] for x in results if x.get("_id")][:ctx.limits["URLSCAN_DETAIL_MAX"]]
                t0, ok, fails, last = time.time(), 0, 0, ""
                for sid in ids:                       # circuit breaker: 2 falhas seguidas e para (evita 12 erros em fila)
                    try:
                        out += enrichment.durable_obs(d, urlscan.result(sid, S.get("URLSCAN_API_KEY", "")) or {}); ok += 1; fails = 0
                    except Exception as exc:
                        fails += 1; last = describe_error(exc)
                        if fails >= 2:
                            break
                if ids:
                    state = "OK" if ok else "UNAVAILABLE"
                    extra.append(status_row("urlscan:detalhes", d, state, ok, time.time() - t0,
                                            "" if ok else f"{last}; consulta interrompida após 2 falhas seguidas"))
            return out, extra
        tasks.append(Task("urlscan", d, urlscan_fn))

    if f["ENABLE_OTX"]:
        def otx_fn():
            o = threatintel.otx_domain(d) or {}
            return [_o(d, "domain", "otx", r["url"]) for r in (o.get("url_list", []) if isinstance(o, dict) else [])[:200]
                    if isinstance(r, dict) and r.get("url")]
        tasks.append(Task("otx", d, otx_fn))

    if f["ENABLE_WAYBACK"]:
        tasks.append(Task("wayback", d, lambda: enrichment.wayback_obs(d, history.wayback(d, 500) or [])))
    if f["ENABLE_COMMONCRAWL"]:
        tasks.append(Task("commoncrawl", d, lambda: enrichment.commoncrawl_obs(d, history.commoncrawl(d, 500) or [])))
    if f["ENABLE_VT"]:
        tasks.append(Task("virustotal", d, lambda: enrichment.virustotal_obs(d, threatintel.virustotal_domain(d, S["VT_API_KEY"]) or {})))
    if f["ENABLE_THREATFOX"]:
        tasks.append(Task("threatfox", d, lambda: enrichment.threatfox_obs(d, threatintel.threatfox_search(d, S["THREATFOX_AUTH_KEY"]) or {})))
    return tasks


def _ip_tasks(ctx: Ctx, ip: str) -> List[Task]:
    f, S, tasks = ctx.feats, ctx.secrets, []
    own = ctx.ownership.setdefault(ip, {"ptr": [], "rdap_ip": {}, "hosted_domains": []})
    if f["ENABLE_PTR"]:
        def ptr_fn():
            own["ptr"] = dns.reverse_ptr(ip) or []
            return enrichment.ptr_obs(ip, own["ptr"])
        tasks.append(Task("dns:PTR", ip, ptr_fn))
    if f["ENABLE_RDAP_IP"]:
        def rdap_fn():
            own["rdap_ip"] = rdap.lookup_ip(ip) or {}
            return enrichment.rdap_ip_obs(ip, own["rdap_ip"])
        tasks.append(Task("rdap_ip", ip, rdap_fn))
    if f["ENABLE_URLSCAN_IP"]:
        def us_fn():
            data = urlscan.search_ip(ip, S.get("URLSCAN_API_KEY", "")) or {}
            obs = enrichment.urlscan_ip_obs(ip, data)
            own["hosted_domains"] = sorted({o.value for o in obs if o.source == "urlscan:hosted_domain"})
            return obs
        tasks.append(Task("urlscan_ip", ip, us_fn))
    if f["ENABLE_VT"]:
        tasks.append(Task("virustotal", ip, lambda: enrichment.virustotal_obs(ip, threatintel.virustotal_ip(ip, S["VT_API_KEY"]) or {}, "ip")))
    if f["ENABLE_THREATFOX"]:
        tasks.append(Task("threatfox", ip, lambda: enrichment.threatfox_obs(ip, threatintel.threatfox_search(ip, S["THREATFOX_AUTH_KEY"]) or {}, "ip")))
    return tasks


def _hash_tasks(ctx: Ctx, h: str) -> List[Task]:
    f, S, tasks = ctx.feats, ctx.secrets, []
    if f["ENABLE_VT"]:
        tasks.append(Task("virustotal", h, lambda: enrichment.virustotal_obs(h, threatintel.virustotal_file(h, S["VT_API_KEY"]) or {}, "hash")))
    if f["ENABLE_THREATFOX"]:
        tasks.append(Task("threatfox", h, lambda: enrichment.threatfox_obs(h, threatintel.threatfox_search(h, S["THREATFOX_AUTH_KEY"]) or {}, "hash")))
    return tasks


def plan_investigation(target: Target, mode: str, budget: str, secrets: Dict[str, str]):
    """Devolve (ctx, tarefas, linhas de fontes puladas). Não faz rede."""
    kinds = target.kinds_present
    feats = features_for_target(kinds, mode, budget, secrets)
    ctx = Ctx(target, secrets, feats, budget_limits(budget, len(target.domains) + len(target.ips)))
    tasks: List[Task] = []
    for d in target.domains:
        tasks += _domain_tasks(ctx, d)
    for ip in target.ips:
        tasks += _ip_tasks(ctx, ip)
    for h in target.hashes:
        tasks += _hash_tasks(ctx, h)
    skipped = []
    for name in SOURCE_FLAGS:
        why = skip_reason(name, kinds, mode, secrets)
        if why:
            skipped.append(skipped_row(name, "—", why[0], why[1]))
    if not tasks:
        reason = {"PHONE": "telefone: " + DOMAIN_ONLY_NOTE, "EMAIL": "e-mail sem domínio público para consultar: " + DOMAIN_ONLY_NOTE,
                  "LURE_TEXT": "o texto não contém domínio, IP ou hash para consultar; a extração de entidades roda mesmo assim",
                  "HASH": "hash: configure VT_API_KEY ou THREATFOX_AUTH_KEY para consultar inteligência de ameaças"}.get(
                      target.kind, "nada a consultar neste alvo")
        skipped.append(skipped_row("coleta", "—", "NOT_NEEDED", reason))
    return ctx, tasks, skipped


# --- etapas pós-coleta -------------------------------------------------------------------------------------------

def _decisions(target: Target, obs: List[Observation], case_id: str, ownership: Dict[str, Any]):
    actionable, context = partition_iocs({k: v for k, v in target.iocs.items() if k in ("domain", "url", "ip", "email", "hash", "phone")})
    cands = []
    for typ, values in actionable.items():
        for value in values:
            matching = [o for o in obs if o.entity == value or o.value == value]
            families = len({o.source.split(":")[0] for o in matching})
            bad = any((o.source.startswith("virustotal:malicious") and str(o.value).isdigit() and int(o.value) > 0) or o.source == "threatfox"
                      for o in obs if o.entity == value or (typ == "url" and o.entity in target.domains))
            conf = min(.70 if bad else .55, .15 + min(.20, len(matching) * .025) + min(.20, families * .05) + (.15 if bad else 0))
            resolves = bool((ownership.get(value, {}).get("dns", {}) or {}).get("A") or (ownership.get(value, {}).get("dns", {}) or {}).get("AAAA"))
            cands.append({"value": value, "type": typ, "confidence": conf, "active": resolves, "evidence_count": len(matching),
                          "source_families": families, "campaign": case_id, "context": {},
                          "rationale": ["Triagem rápida; validação do analista necessária"] + (["Sinal malicioso em fonte de ameaças"] if bad else [])})
    return build_ioc_decisions(cands, WarningListEngine()), context


def _entities(target: Target, ledger, ai_mode: str):
    gliner, note = None, "regras"
    if ai_mode != "OFF":
        try:
            from .ai import GLiNERLocal
            gliner = GLiNERLocal(); gliner.load(); note = "regras + GLiNER"
        except Exception as exc:
            gliner, note = None, "regras (GLiNER indisponível: " + str(exc)[:120] + ")"
    from .ai import correlate_entities, extract_hybrid
    ents = extract_hybrid(target.lure_text, gliner) if target.lure_text else []
    known = set(ledger["entity"]) | set(ledger["value"]) if not ledger.empty else set()
    return gliner, note, ents, correlate_entities(ents, known), detect_br_lures(target.lure_text)


def _ai_stage(report_data, target, gliner, ai_mode):
    summary, entities, status = {}, [], "IA desligada"
    if ai_mode == "OFF":
        return report_data, summary, entities, status
    try:
        from .ai import (GLiNERLocal, QwenLocalChat, attach_ai_overlay, build_ai_text_corpus, build_evidence_packet,
                         run_qwen_analysis, runtime_profile)
        corpus = build_ai_text_corpus(report_data, target.text if target.kind == "LURE_TEXT" else "", "")
        gliner = gliner or GLiNERLocal()
        entities = gliner.extract(corpus)
        status = f"GLiNER: {len(entities)} entidades candidatas"
        if ai_mode in {"GLINER_QWEN", "AUTO"} and (ai_mode == "GLINER_QWEN" or runtime_profile().get("gpu")):
            packet = build_evidence_packet(report_data)
            qwen = QwenLocalChat()
            summary = run_qwen_analysis(qwen, packet, language="pt-BR", max_new_tokens=900)
            report_data = attach_ai_overlay(report_data, entities, summary, {"frontend_ai": status}, packet)
            status += f" · Qwen ({qwen.model_name}) concluído" + (" — modelo pequeno: revise sempre a análise" if "0.6B" in qwen.model_name else "")
        else:
            report_data = attach_ai_overlay(report_data, entities, {}, {"frontend_ai": status})
    except Exception as exc:
        status = "IA indisponível: " + str(exc)[:300]
    return report_data, summary, entities, status


def _memory_stage(report_data, target, case_id, enabled, path):
    matches, prevalence, similar = [], [], []
    resolved = (path or "").strip() or str(default_memory_path())
    if not enabled:
        report_data["cross_case_intelligence"] = {"status": "DISABLED", "related_cases": [], "artifact_prevalence": []}
        return matches, prevalence, similar, ""
    try:
        from .ai import lure_similarity
        memory = CaseMemory(resolved)
        matches = memory.compare_report(report_data, exclude_case_id=case_id, limit=10)
        prevalence = memory.prevalence_for_report(report_data, exclude_case_id=case_id)[:200]
        report_data["cross_case_intelligence"] = {"status": "OK", "related_cases": matches, "artifact_prevalence": prevalence,
                                                  "memory_stats": memory.stats(), "same_operator_inferred": False}
        if target.lure_text:
            similar = lure_similarity(target.lure_text, memory.lure_texts(exclude_case_id=case_id))
        # o texto da isca fica só no banco local, nunca no case.json exportado
        memory.store_case({**report_data, "lure_text": target.lure_text} if target.lure_text else report_data)
        report_data["cross_case_intelligence"]["memory_stats"] = memory.stats()
    except Exception as exc:
        report_data["cross_case_intelligence"] = {"status": "UNAVAILABLE", "error": str(exc)[:400], "related_cases": [], "artifact_prevalence": []}
    return matches, prevalence, similar, resolved


def _export_stage(report_data, target, case_id, workspace: Path):
    report_dir = workspace / "report"; report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "Tropeiro_Intel_Report.html"
    build_report(report_data, report_path)
    export_dir = workspace / "export"
    created = export_selected(report_data, export_dir, {"report_html", "case_json", "evidence_ledger_csv", "ioc_decisions_csv"}, report_path)
    act, ctx = partition_iocs({k: v for k, v in target.iocs.items() if k in ("domain", "url", "ip", "email", "hash", "phone")})
    (export_dir / "stix.json").write_text(bundle_from_iocs(act, case_id=case_id, context_only=ctx).serialize(pretty=True), encoding="utf-8")
    (export_dir / "misp.json").write_text(json.dumps(misp_event(case_id, act, context_only=ctx), ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in sigma_rules(act, case_id).items():
        (export_dir / f"sigma_{k}.yml").write_text(v + "\n", encoding="utf-8")
    cti = [export_dir / n for n in ("stix.json", "misp.json")] + sorted(export_dir.glob("sigma_*.yml"))
    created = [c for c in created if Path(c).name != "manifest.json"] + cti
    created.append(write_manifest(created, export_dir))
    zip_path = zip_exports(created, workspace / f"Tropeiro_{case_id}_Package.zip")
    return report_path, zip_path, [str(x) for x in cti]


# --- API pública -------------------------------------------------------------------------------------------------------

def default_base() -> Path:
    """Pasta-base dos casos: TROPEIRO_WORKSPACE, ou /content (Colab), ou a pasta temporária do sistema."""
    import os
    env = os.getenv("TROPEIRO_WORKSPACE", "").strip()
    if env:
        return Path(env).expanduser()
    return Path("/content") if Path("/content").is_dir() else Path(tempfile.gettempdir())


def investigate(target: str, target_type: str = "AUTO", case_id: str = "TI-UI-001", analyst: str = "Analista",
                brand: str = "", impersonated_org: str = "", mode: str = "PASSIVE", budget: str = "balanced",
                ai_mode: str = "OFF", memory_enabled: bool = True, memory_path: str = "", progress: Progress = None,
                workspace: Optional[Path] = None, deadline: Optional[float] = None, secrets: Optional[Dict[str, str]] = None,
                use_cache: bool = True, on_source: Optional[Callable[[dict], None]] = None,
                on_plan: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
    """Executa uma investigação completa e devolve o resultado (ver `docs/PYTHON_API.md`)."""
    if not (target or "").strip():
        raise ValueError("Informe um domínio, URL, IP, e-mail, hash, telefone ou texto.")
    t0 = time.time()
    step = (lambda frac, msg: progress(frac, desc=msg)) if progress else (lambda frac, msg: None)
    step(.03, "Preparando o caso")
    tgt = parse_target(target, target_type)
    case_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", case_id or "TI-UI-001")
    base = default_base()
    workspace = Path(workspace) if workspace else base / f"tropeiro_ui_{case_id}"
    workspace.mkdir(parents=True, exist_ok=True)
    if use_cache:
        http.set_cache(base / ".tropeiro_cache" if base == Path("/content") else Path.home() / ".tropeiro" / "cache", ttl=3600)
    secrets = secrets if secrets is not None else {k: secret(k) for k in SECRET_NAMES}
    settings = Settings(case_id=case_id, analyst=analyst or "Analista", brand=brand or "", workspace=workspace, mode=mode, provider_budget=budget)

    ctx, tasks, skipped = plan_investigation(tgt, mode, budget, secrets)
    if on_plan:
        on_plan(len(tasks))
    deadline = float(deadline) if deadline else BUDGET_DEADLINE.get(budget, 90.0)
    obs: List[Observation] = []
    for typ, values in tgt.iocs.items():
        for value in values:
            obs.append(Observation(str(value), typ, "manual/input", str(value), confidence="observed", notes="Entrada do analista"))

    step(.10, f"Consultando {len(tasks)} fontes em paralelo (prazo {deadline:.0f}s)")
    def on_progress(done, total, row):
        step(.10 + .45 * done / max(1, total), f"Fontes {done}/{total} · {row['source']} {row['subject']}: {row['status']}")
        if on_source:
            on_source(row)
    collected, status = run_tasks(tasks, deadline=deadline, max_workers=settings.max_workers, on_progress=on_progress)
    obs += collected
    status = status + skipped

    step(.58, "Montando evidências")
    ledger = build_ledger(obs, settings.source_reliability)
    rels = relationship_rows(ctx.ownership)
    batches = registration_batches(ctx.rdap_rows)
    decisions, context_iocs = _decisions(tgt, obs, case_id, ctx.ownership)

    step(.62, "Extraindo e correlacionando entidades")
    gliner, hybrid_note, hybrid_entities, ai_edges, lures = _entities(tgt, ledger, ai_mode)

    label = tgt.text[:120] + ("…" if len(tgt.text) > 120 else "")
    if tgt.lure_text and lures:                    # título curto e útil em vez do texto inteiro da mensagem
        label = "Isca «" + "; ".join(dict.fromkeys(x["brand"] for x in lures)) + "» · " + "; ".join(dict.fromkeys(x["theme"] for x in lures))
    ns = {"CASE_ID": case_id, "ANALYST": analyst, "BRAND": brand, "IMPERSONATED_ORG": impersonated_org, "MODE": mode,
          "WORKSPACE": workspace, "STATUS": status, "OWNERSHIP": ctx.ownership, "LEDGER_DF": ledger, "IOC_DECISIONS": decisions,
          "RELATIONSHIP_GRAPH": {"nodes": [], "edges": rels},
          "EXECUTIVE_ASSESSMENT": {"judgment": f"Investigação rápida de {label}",
                                   "implication": "Revise a evidência e a saúde das fontes antes de qualquer ação operacional."}}
    report_data = build_report_data(ns, version=__version__)

    if ai_mode != "OFF":
        step(.70, "Executando camada de IA")
    report_data, ai_summary, ai_entities, ai_status = _ai_stage(report_data, tgt, gliner, ai_mode)

    step(.80, "Comparando com casos anteriores")
    matches, prevalence, similar_lures, resolved_memory = _memory_stage(report_data, tgt, case_id, memory_enabled, memory_path)

    step(.88, "Gerando relatório e exportações")
    report_path, zip_path, cti_files = _export_stage(report_data, tgt, case_id, workspace)
    step(1.0, "Concluído")

    ok = sum(1 for x in status if x["status"] == "OK")
    failed = sum(1 for x in status if x["status"] in ("UNAVAILABLE", "TIMEOUT"))
    summary = {
        "case_id": case_id, "input_type": tgt.kind, "target": label, "domains": tgt.domains, "ips": tgt.ips, "hashes": tgt.hashes,
        "observations": len(obs), "evidence": len(ledger), "relationships": len(rels),
        "sources_ok": ok, "sources_failed": failed, "sources_skipped": len(status) - ok - failed,
        "ai": f"{ai_status} · extração: {hybrid_note}", "memory_matches": len(matches), "memory_path": resolved_memory,
        "report": str(report_path), "elapsed_s": round(time.time() - t0, 1), "deadline_s": deadline, "mode": mode, "budget": budget,
        "context_only": sum(len(v) for v in context_iocs.values()),
    }
    return {
        "summary": summary, "iocs": decisions, "context_iocs": context_iocs, "relationships": rels,
        "evidence": ledger.to_dict("records") if not ledger.empty else [], "sources": status,
        "ai_entities": ai_entities, "hybrid_entities": hybrid_entities, "ai_edges": ai_edges, "lures": lures,
        "timeline_md": timeline_markdown(build_timeline(ledger)), "related_cases": matches, "artifact_prevalence": prevalence,
        "exports": cti_files, "batches": batches, "similar_lures": similar_lures, "ai_analysis": ai_summary,
        "report_path": str(report_path), "package_path": str(zip_path),
        "plan": [{"source": t.source, "subject": t.subject} for t in tasks],
    }

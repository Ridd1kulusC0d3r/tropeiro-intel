from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from ..models import Observation, now_iso
from ..utils import extract_iocs, hostname, root_domain
from ..config import Settings
from ..collectors import dns, rdap, crtsh, urlscan, threatintel
from ..evidence.ledger import build as build_ledger
from ..intelligence.warninglists import WarningListEngine
from ..intelligence.decision_objects import build_ioc_decisions
from ..reporting.context import build_report_data
from ..reporting.rich_html import build_report
from ..reporting.exporter import export_selected, zip_exports
from ..onboarding import detect_input_type
from ..memory import CaseMemory, default_memory_path
from ..ai import (
    GLiNERLocal, QwenLocalChat, build_ai_text_corpus, build_evidence_packet,
    run_qwen_analysis, attach_ai_overlay, runtime_profile
)

APP_CSS = """
:root { --bg:#0a0b0c; --panel:#111315; --line:#2a2d31; --muted:#969da5; --ink:#f4f5f6; }
.gradio-container { max-width: 1500px !important; margin: 0 auto !important; background: var(--bg) !important; }
#ti-hero { padding:26px 8px 8px; }
#ti-hero h1 { font-size:42px; line-height:1.05; margin:0 0 8px; letter-spacing:-.04em; }
#ti-hero p { color:var(--muted); max-width:850px; font-size:15px; }
.ti-card { border:1px solid var(--line) !important; border-radius:14px !important; background:var(--panel) !important; }
.ti-note { color:var(--muted); font-size:12px; }
footer { display:none !important; }
"""

def _secret(name: str) -> str:
    try:
        from google.colab import userdata
        return userdata.get(name) or ""
    except Exception:
        return os.getenv(name,"")

def _safe(source: str, fn, status: List[Dict[str,Any]], *args, **kwargs):
    t=time.time()
    try:
        value=fn(*args,**kwargs)
        size=len(value) if hasattr(value,"__len__") else 1
        status.append({"source":source,"status":"OK","items":size,"seconds":round(time.time()-t,2),"error":""})
        return value
    except Exception as exc:
        status.append({"source":source,"status":"UNAVAILABLE","items":0,"seconds":round(time.time()-t,2),"error":str(exc)[:260]})
        return None

def _observe(rows: List[Observation], entity, entity_type, source, value, confidence="observed", notes=""):
    rows.append(Observation(str(entity),str(entity_type),str(source),str(value),confidence=confidence,notes=str(notes)))

def relationship_rows(ownership: Dict[str,Any]) -> List[Dict[str,Any]]:
    rows=[]
    for domain,data in (ownership or {}).items():
        for rtype,values in (data.get("dns") or {}).items():
            for value in values or []:
                rows.append({"from":domain,"relationship":f"dns_{rtype.lower()}","to":value,"source":f"dns:{rtype}"})
        for org in (data.get("rdap") or {}).get("registrant_orgs",[]) or []:
            rows.append({"from":domain,"relationship":"registrant_org","to":org,"source":"rdap"})
        for name in data.get("cert_names",[])[:100]:
            if name and name!=domain:
                rows.append({"from":domain,"relationship":"certificate_name","to":name,"source":"crt.sh"})
    return rows

def _normalize_target(target: str, selected_type: str) -> Tuple[str,Dict[str,List[str]]]:
    kind=detect_input_type(target) if selected_type=="AUTO" else selected_type
    iocs=extract_iocs(target)
    if kind=="DOMAIN" and target.strip():
        iocs.setdefault("domain",[])
        iocs["domain"]=sorted(set(iocs["domain"]+[hostname(target.strip())]))
    elif kind=="URL" and target.strip():
        iocs.setdefault("url",[])
        iocs["url"]=sorted(set(iocs["url"]+[target.strip()]))
        h=hostname(target.strip())
        if h:
            iocs.setdefault("domain",[])
            iocs["domain"]=sorted(set(iocs["domain"]+[h]))
    elif kind=="IP":
        iocs.setdefault("ip",[])
        iocs["ip"]=sorted(set(iocs["ip"]+[target.strip()]))
    elif kind=="EMAIL":
        iocs.setdefault("email",[])
        iocs["email"]=sorted(set(iocs["email"]+[target.strip().lower()]))
    elif kind=="HASH":
        iocs.setdefault("hash",[])
        iocs["hash"]=sorted(set(iocs["hash"]+[target.strip().lower()]))
    elif kind=="PHONE":
        digits=re.sub(r"\D","",target)
        iocs.setdefault("phone",[])
        iocs["phone"]=sorted(set(iocs["phone"]+[digits]))
    return kind,iocs

def run_quick_case(
    target: str,
    target_type: str="AUTO",
    case_id: str="TI-UI-001",
    analyst: str="Analista",
    brand: str="",
    impersonated_org: str="",
    mode: str="PASSIVE",
    budget: str="balanced",
    ai_mode: str="OFF",
    memory_enabled: bool=True,
    memory_path: str="",
    progress=None,
):
    if not (target or "").strip():
        raise ValueError("Informe um domínio, URL, IP, e-mail, hash, telefone ou texto.")

    def step(frac,msg):
        if progress is not None:
            progress(frac,desc=msg)

    step(.03,"Preparando o caso")
    kind,iocs=_normalize_target(target,target_type)
    case_id=re.sub(r"[^A-Za-z0-9_.-]+","_",case_id or "TI-UI-001")
    workspace=Path("/content")/f"tropeiro_ui_{case_id}"
    workspace.mkdir(parents=True,exist_ok=True)
    settings=Settings(case_id=case_id,analyst=analyst or "Analista",brand=brand or "",workspace=workspace,mode=mode,provider_budget=budget)

    obs: List[Observation]=[]
    status=[]
    ownership={}
    for typ,values in iocs.items():
        for value in values:
            _observe(obs,value,typ,"manual/input",value,notes="Frontend guided input")

    domains=sorted(set(root_domain(x) for x in iocs.get("domain",[]) if root_domain(x)))
    step(.12,"DNS, RDAP e certificados")

    for idx,domain in enumerate(domains):
        data={"domain":domain,"dns":{},"rdap":{},"cert_names":[]}
        ownership[domain]=data
        for rtype in ("A","AAAA","CNAME","MX","NS"):
            values=_safe(f"dns:{rtype}",dns.query,status,domain,rtype) or []
            data["dns"][rtype]=values
            for value in values:
                _observe(obs,domain,"domain",f"dns:{rtype}",value)
        r=_safe("rdap",rdap.lookup,status,domain) or {}
        data["rdap"]=r
        for org in r.get("registrant_orgs",[]) or []:
            _observe(obs,domain,"domain","rdap:registrant_org",org)
        for org in r.get("registrar_orgs",[]) or []:
            _observe(obs,domain,"domain","rdap:registrar_org",org)
        ct=_safe("crt.sh",crtsh.lookup,status,domain) or []
        names=set()
        for row in ct if isinstance(ct,list) else []:
            for name in str(row.get("name_value","")).splitlines():
                name=name.strip().lower().lstrip("*.")
                if name:
                    names.add(name)
        data["cert_names"]=sorted(names)[:500]
        for name in data["cert_names"]:
            _observe(obs,domain,"domain","crt.sh",name)

        step(.25 + (.20*((idx+1)/max(1,len(domains)))),"Enriquecendo fontes públicas")
        u=_safe("urlscan",urlscan.search,status,domain,_secret("URLSCAN_API_KEY")) or {}
        for row in (u.get("results",[]) if isinstance(u,dict) else [])[:100]:
            page=row.get("page",{});task=row.get("task",{})
            value=page.get("url") or task.get("url")
            if value:
                _observe(obs,domain,"domain","urlscan",value)
        o=_safe("otx",threatintel.otx_domain,status,domain) or {}
        for row in (o.get("url_list",[]) if isinstance(o,dict) else [])[:200]:
            value=row.get("url") if isinstance(row,dict) else None
            if value:
                _observe(obs,domain,"domain","otx",value)

    step(.52,"Montando evidências")
    ledger=build_ledger(obs,settings.source_reliability)
    rels=relationship_rows(ownership)

    ioc_candidates=[]
    for typ,values in iocs.items():
        for value in values:
            matching=[o for o in obs if o.entity==value or o.value==value]
            families=len(set(o.source.split(":")[0] for o in matching))
            conf=min(.55,.15 + min(.20,len(matching)*.025) + min(.20,families*.05))
            ioc_candidates.append({
                "value":value,"type":typ,"confidence":conf,"active":False,
                "evidence_count":len(matching),"source_families":families,
                "campaign":case_id,"context":{},"rationale":["Quick UI triage; analyst validation required"]
            })
    decisions=build_ioc_decisions(ioc_candidates,WarningListEngine())

    ns={
        "CASE_ID":case_id,"ANALYST":analyst,"BRAND":brand,"IMPERSONATED_ORG":impersonated_org,
        "MODE":mode,"WORKSPACE":workspace,"STATUS":status,"OWNERSHIP":ownership,
        "LEDGER_DF":ledger,"IOC_DECISIONS":decisions,
        "RELATIONSHIP_GRAPH":{"nodes":[],"edges":rels},
        "EXECUTIVE_ASSESSMENT":{
            "judgment":f"Quick investigation of {target}",
            "implication":"Review evidence and source health before operational action."
        },
    }
    report_data=build_report_data(ns,version="frontend")

    ai_summary={}
    ai_entities=[]
    ai_status="AI desligada"
    if ai_mode!="OFF":
        step(.68,"Executando camada de IA")
        try:
            corpus=build_ai_text_corpus(report_data,target if kind=="LURE_TEXT" else "","")
            gliner=GLiNERLocal()
            ai_entities=gliner.extract(corpus)
            ai_status=f"GLiNER: {len(ai_entities)} entidades candidatas"
            if ai_mode in {"GLINER_QWEN","AUTO"} and (ai_mode=="GLINER_QWEN" or runtime_profile().get("gpu")):
                packet=build_evidence_packet(report_data)
                qwen=QwenLocalChat()
                ai_summary=run_qwen_analysis(qwen,packet,language="pt-BR",max_new_tokens=900)
                report_data=attach_ai_overlay(report_data,ai_entities,ai_summary,{"frontend_ai":ai_status},packet)
                ai_status+=" · Qwen concluído"
            else:
                report_data=attach_ai_overlay(report_data,ai_entities,{},{"frontend_ai":ai_status})
        except Exception as exc:
            ai_status="IA indisponível: "+str(exc)[:300]

    step(.76,"Comparando com casos anteriores")
    memory_matches=[];artifact_prevalence=[];memory_stats={}
    resolved_memory_path=(memory_path or "").strip() or str(default_memory_path())
    if memory_enabled:
        try:
            memory=CaseMemory(resolved_memory_path)
            memory_matches=memory.compare_report(report_data,exclude_case_id=case_id,limit=10)
            artifact_prevalence=memory.prevalence_for_report(report_data,exclude_case_id=case_id)[:200]
            memory_stats=memory.stats()
            report_data["cross_case_intelligence"]={
                "status":"OK","related_cases":memory_matches,
                "artifact_prevalence":artifact_prevalence,
                "memory_stats":memory_stats,"same_operator_inferred":False
            }
            memory.store_case(report_data)
            memory_stats=memory.stats()
            report_data["cross_case_intelligence"]["memory_stats"]=memory_stats
        except Exception as exc:
            report_data["cross_case_intelligence"]={
                "status":"UNAVAILABLE","error":str(exc)[:400],
                "related_cases":[],"artifact_prevalence":[]
            }
    else:
        resolved_memory_path=""
        report_data["cross_case_intelligence"]={
            "status":"DISABLED","related_cases":[],"artifact_prevalence":[]
        }

    step(.82,"Gerando relatório")
    report_dir=workspace/"report"
    report_dir.mkdir(parents=True,exist_ok=True)
    report_path=report_dir/"Tropeiro_Intel_Report.html"
    build_report(report_data,report_path)

    created=export_selected(
        report_data,workspace/"export",
        {"report_html","case_json","evidence_ledger_csv","ioc_decisions_csv"},
        report_path
    )
    zip_path=zip_exports(created,workspace/f"Tropeiro_{case_id}_Package.zip")

    step(1.0,"Concluído")
    summary={
        "case_id":case_id,"input_type":kind,"target":target,"domains":domains,
        "observations":len(obs),"evidence":len(ledger),"relationships":len(rels),
        "sources_ok":sum(1 for x in status if x.get("status")=="OK"),
        "sources_failed":sum(1 for x in status if x.get("status")!="OK"),
        "ai":ai_status,
        "memory_matches":len(memory_matches),"memory_path":resolved_memory_path,
        "report":str(report_path)
    }
    return {
        "summary":summary,
        "iocs":decisions,
        "relationships":rels,
        "evidence":ledger.to_dict("records") if not ledger.empty else [],
        "sources":status,
        "ai_entities":ai_entities,
        "ai_analysis":ai_summary,
        "report_path":str(report_path),
        "package_path":str(zip_path),
    }

def _df(rows):
    if not rows:
        return pd.DataFrame()
    if isinstance(rows,pd.DataFrame):
        return rows
    return pd.DataFrame(rows)

def launch_colab_frontend(server_port: int=7860, inline: bool=True):
    import gradio as gr

    def execute(target,target_type,case_id,analyst,brand,org,mode,budget,ai_mode,memory_enabled,memory_path,progress=gr.Progress()):
        result=run_quick_case(target,target_type,case_id,analyst,brand,org,mode,budget,ai_mode,memory_enabled,memory_path,progress)
        s=result["summary"]
        summary_html=f"""
        <div class='ti-card' style='padding:18px'>
          <div style='font-size:12px;color:#969da5;text-transform:uppercase;letter-spacing:.12em'>Investigation complete</div>
          <h2 style='margin:6px 0 12px'>{s['target']}</h2>
          <div style='display:flex;gap:22px;flex-wrap:wrap'>
            <div><b>{s['evidence']}</b><br><span class='ti-note'>evidências</span></div>
            <div><b>{s['relationships']}</b><br><span class='ti-note'>relações</span></div>
            <div><b>{s['sources_ok']}</b><br><span class='ti-note'>fontes OK</span></div>
            <div><b>{s['sources_failed']}</b><br><span class='ti-note'>fontes indisponíveis</span></div>
            <div><b>{s.get('memory_matches',0)}</b><br><span class='ti-note'>casos relacionados</span></div>
          </div>
          <p class='ti-note' style='margin-top:14px'>{s['ai']}</p>
        </div>
        """
        return (
            summary_html,
            _df(result["iocs"]),
            _df(result["relationships"]),
            _df(result["evidence"]),
            _df(result["sources"]),
            _df(result["ai_entities"]),
            result["ai_analysis"],
            _df(result["related_cases"]),
            _df(result["artifact_prevalence"]),
            result["report_path"],
            result["package_path"],
        )

    with gr.Blocks(css=APP_CSS,title="Tropeiro Intel · Investigation Workbench") as app:
        gr.HTML("""<div id='ti-hero'><div style='font:600 11px ui-monospace;letter-spacing:.14em;color:#969da5'>TROPEIRO · OPEN-SOURCE INTELLIGENCE</div><h1>Investigation Workbench</h1><p>Cole um alvo, execute a investigação e leia evidência, relações e relatório sem precisar operar as células avançadas do notebook.</p></div>""")
        with gr.Row():
            with gr.Column(scale=1,min_width=360,elem_classes=["ti-card"]):
                gr.Markdown("### Nova investigação")
                target_type=gr.Dropdown(
                    choices=["AUTO","DOMAIN","URL","IP","EMAIL","HASH","PHONE","MULTI_IOC","LURE_TEXT"],
                    value="AUTO",label="Tipo de busca"
                )
                target=gr.Textbox(label="Alvo da investigação",placeholder="ex.: dominio-suspeito.com",lines=3)
                with gr.Row():
                    case_id=gr.Textbox(value="TI-UI-001",label="ID do caso")
                    analyst=gr.Textbox(value="Analista",label="Analista")
                brand=gr.Textbox(label="Marca (opcional)",placeholder="ex.: WhatsApp")
                org=gr.Textbox(label="Organização imitada (opcional)",placeholder="ex.: Meta")
                with gr.Row():
                    mode=gr.Dropdown(["PASSIVE","SAFE_ENRICHMENT","AUTHORIZED_ACTIVE"],value="PASSIVE",label="Modo")
                    budget=gr.Dropdown(["free","balanced","extended"],value="balanced",label="Profundidade")
                ai_mode=gr.Dropdown(["OFF","GLINER_ONLY","GLINER_QWEN","AUTO"],value="OFF",label="IA")
                memory_enabled=gr.Checkbox(value=True,label="Usar Campaign Memory")
                memory_path=gr.Textbox(label="Arquivo da memória (opcional)",placeholder="/content/tropeiro_case_memory.sqlite ou caminho no Google Drive")
                run=gr.Button("Executar investigação",variant="primary")
                gr.Markdown("**Recomendado para iniciantes:** PASSIVE · balanced · IA OFF/AUTO. E-mail e telefone são tratados apenas como IOCs já observados, sem busca de dados privados.")
            with gr.Column(scale=2):
                summary=gr.HTML("<div class='ti-card' style='padding:22px'><b>Aguardando investigação.</b><br><span class='ti-note'>Preencha o alvo à esquerda e clique em Executar investigação.</span></div>")
                with gr.Tabs():
                    with gr.Tab("IOCs"):
                        ioc_table=gr.Dataframe(interactive=False,wrap=True)
                    with gr.Tab("Relações"):
                        rel_table=gr.Dataframe(interactive=False,wrap=True)
                    with gr.Tab("Evidências"):
                        ev_table=gr.Dataframe(interactive=False,wrap=True)
                    with gr.Tab("Fontes"):
                        source_table=gr.Dataframe(interactive=False,wrap=True)
                    with gr.Tab("IA"):
                        ai_table=gr.Dataframe(interactive=False,wrap=True,label="Entidades GLiNER")
                        ai_json=gr.JSON(label="Análise Qwen")
                    with gr.Tab("Memória"):
                        related_table=gr.Dataframe(interactive=False,wrap=True,label="Casos relacionados")
                        prevalence_table=gr.Dataframe(interactive=False,wrap=True,label="Prevalência / raridade")
                    with gr.Tab("Relatório"):
                        report_file=gr.File(label="Relatório HTML")
                        package_file=gr.File(label="Pacote completo ZIP")

        run.click(
            execute,
            inputs=[target,target_type,case_id,analyst,brand,org,mode,budget,ai_mode,memory_enabled,memory_path],
            outputs=[summary,ioc_table,rel_table,ev_table,source_table,ai_table,ai_json,related_table,prevalence_table,report_file,package_file],
        )

    app.launch(
        server_name="0.0.0.0",
        server_port=server_port,
        share=False,
        inline=inline,
        prevent_thread_lock=True,
        show_error=True,
    )
    return app

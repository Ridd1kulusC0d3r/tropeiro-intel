"""Workbench (Gradio): camada fina sobre `tropeiro.pipeline`. Toda a lógica de investigação vive no pipeline."""
from __future__ import annotations

import queue, shutil, socket, tempfile, threading, time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from ..doctor import run_checks
from ..pipeline import default_base, investigate, relationship_rows          # noqa: F401  (relationship_rows é reexportado: API estável)
from ..sources import BUDGET_DEADLINE
from ..targets import parse_target
from .views import (APP_CSS, HERO, IOC_COLS, diagnostics_html, edges_rows, error_html, graph_svg, ioc_rows, kpi_html, lure_html,
                    progress_html, source_rows)


def run_quick_case(*args, **kwargs):
    """Compatibilidade: a investigação do Workbench é a `pipeline.investigate`."""
    return investigate(*args, **kwargs)


def _normalize_target(target: str, selected_type: str = "AUTO") -> Tuple[str, Dict[str, List[str]]]:
    """Compatibilidade: (tipo, iocs) de um alvo. A lógica está em `tropeiro.targets.parse_target`."""
    t = parse_target(target, selected_type)
    return t.kind, t.iocs


def _df(rows, cols=None):
    """DataFrame para a tabela; vazio, mantém os cabeçalhos (senão o Gradio mostra colunas "1 2 3")."""
    if isinstance(rows, pd.DataFrame):
        return rows
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=cols) if cols else pd.DataFrame()


def relation_table(rows):
    return [{"de": r["from"], "relação": r["relationship"], "para": r["to"], "fonte": r["source"]} for r in rows or []]


def batch_rows(batches):
    return [{"domínios": ", ".join(b["domains"]), "primeiro": b["first"], "último": b["last"], "registrar": b["registrar"],
             "nameservers": ", ".join(b["nameservers"]), "motivo": b["reason"]} for b in batches or []]


def publish_files(result: Dict[str, Any]) -> Dict[str, Any]:
    """Copia relatório, ZIP e exportações para uma pasta que o Gradio aceita servir (a pasta temporária do sistema).

    O Gradio recusa arquivos fora da pasta atual/temporária (`InvalidPathError`): sem isto, uma pasta de trabalho
    personalizada (TROPEIRO_WORKSPACE, /content, etc.) deixava a tela sem resultado. Os originais não são tocados.
    """
    dest = Path(tempfile.gettempdir()) / "tropeiro_serve" / str(result["summary"]["case_id"])
    dest.mkdir(parents=True, exist_ok=True)

    def copy(p):
        if not p:
            return p
        src = Path(p)
        if not src.is_file():
            return p
        out = dest / src.name
        shutil.copyfile(src, out)
        return str(out)

    return {**result, "exports": [copy(x) for x in result.get("exports") or []],
            "report_path": copy(result.get("report_path")), "package_path": copy(result.get("package_path"))}


def render_outputs(result):
    """Converte o resultado do caso nas saídas da interface (puro: testável sem Gradio)."""
    s = result["summary"]; ents = result.get("hybrid_entities", []); edges = result.get("ai_edges", [])
    return (
        kpi_html(s, ents, edges),
        graph_svg(result["relationships"], edges, ents),
        _df(ioc_rows(result["iocs"]), [c for _, c in IOC_COLS]),
        lure_html(result.get("lures", []), ents),
        _df(edges_rows(edges), ["de", "relação", "para", "score", "extração"]),
        _df(result.get("ai_entities", []), ["value", "label", "score", "source_context"]),
        result.get("ai_analysis") or {},
        _df(relation_table(result["relationships"]), ["de", "relação", "para", "fonte"]),
        _df(result["evidence"], ["evidence_id", "entity", "entity_type", "source", "value", "observed_at"]),
        result.get("timeline_md", "") or "_Sem eventos._",
        _df(source_rows(result["sources"]), ["fonte", "assunto", "estado", "itens", "segundos", "observação"]),
        _df(result.get("related_cases", []), ["case_id", "similarity"]),
        _df(result.get("artifact_prevalence", []), ["artifact_type", "value", "prevalence"]),
        _df(batch_rows(result.get("batches", [])), ["domínios", "primeiro", "último", "registrar", "nameservers", "motivo"]),
        _df(result.get("similar_lures", []), ["case_id", "similarity"]),
        result.get("exports") or [],
        result.get("report_path"),
        result.get("package_path"),
    )


N_OUTPUTS = 18


def stream_investigation(target, target_type, case_id, analyst, brand, org, mode, budget, ai_mode, memory_enabled, memory_path, noop):
    """Gerador usado pelo botão "Executar": mostra a coleta ao vivo (fonte a fonte) e, no fim, os resultados.

    Cada `yield` é uma tupla com as N_OUTPUTS saídas; `noop` é o valor "não mude" do Gradio (`gr.update()`).
    Erros viram um painel na tela, nunca silêncio.
    """
    if not (target or "").strip():
        yield (error_html("Informe um domínio, URL, IP, e-mail, hash, telefone ou o texto da isca."), *noop); return
    rows: List[dict] = []; box: Dict[str, Any] = {}; q: "queue.Queue[dict]" = queue.Queue()
    deadline = BUDGET_DEADLINE.get(budget, 90.0)

    def work():
        try:
            box["r"] = publish_files(investigate(target, target_type, case_id, analyst, brand, org, mode, budget, ai_mode,
                                                 memory_enabled, memory_path, on_source=q.put,
                                                 on_plan=lambda n: box.__setitem__("planned", n)))
        except BaseException as exc:                          # noqa: BLE001 - qualquer falha deve chegar à tela
            box["err"] = exc

    th = threading.Thread(target=work, daemon=True, name="tropeiro-investigation"); th.start()
    t0 = time.time()
    yield (progress_html(0, deadline, rows, 0), *noop)
    while th.is_alive():
        th.join(0.8)
        while not q.empty():
            rows.append(q.get())
        yield (progress_html(time.time() - t0, deadline, rows, box.get("planned", 0)), *noop)
    if "err" in box:
        yield (error_html(f"{type(box['err']).__name__}: {box['err']}"), *noop); return
    yield render_outputs(box["r"])


def build_app():
    import gradio as gr
    from .demo import demo_result, DEMO_LURE

    def execute(*args):
        yield from stream_investigation(*args, noop=[gr.update()] * (N_OUTPUTS - 1))

    def load_demo():
        return (DEMO_LURE, "LURE_TEXT", *render_outputs(demo_result()))

    def diagnose():
        return diagnostics_html(run_checks(network=True, timeout=10.0))

    theme = gr.themes.Base(primary_hue="amber", neutral_hue="slate", font=[gr.themes.Font(f) for f in ("ui-sans-serif", "system-ui", "sans-serif")],
                           font_mono=[gr.themes.Font(f) for f in ("ui-monospace", "Menlo", "monospace")]).set(
        body_background_fill="#0B0D10", body_background_fill_dark="#0B0D10", block_background_fill="#12151A", block_background_fill_dark="#12151A",
        block_border_color="#252A32", block_border_color_dark="#252A32", input_background_fill="#0F1217", input_background_fill_dark="#0F1217",
        button_primary_background_fill="#E8A33D", button_primary_background_fill_dark="#E8A33D",
        button_primary_text_color="#0B0D10", button_primary_text_color_dark="#0B0D10")

    # Gradio >=6 moveu css/theme/js do Blocks() para launch(); guardamos o estilo para o launch.
    style = dict(css=APP_CSS, theme=theme, js="() => { document.body.classList.add('dark'); }")
    legacy = int(gr.__version__.split(".")[0]) < 6
    with gr.Blocks(title="Tropeiro Intel · Investigation Workbench", **(style if legacy else {})) as app:
        gr.HTML(HERO)
        with gr.Row():
            with gr.Column(scale=1, min_width=360, elem_classes=["ti-card"]):
                gr.Markdown("### Nova investigação")
                target_type = gr.Dropdown(choices=["AUTO", "DOMAIN", "URL", "IP", "EMAIL", "HASH", "PHONE", "MULTI_IOC", "LURE_TEXT"], value="AUTO", label="Tipo de busca")
                target = gr.Textbox(label="Alvo da investigação", placeholder="domínio, URL, IP… ou cole o texto da isca (aceita hxxp / [.])", lines=4)
                with gr.Accordion("Opções avançadas", open=False):
                    with gr.Row():
                        case_id = gr.Textbox(value="TI-UI-001", label="ID do caso")
                        analyst = gr.Textbox(value="Analista", label="Analista")
                    brand = gr.Textbox(label="Marca (opcional)", placeholder="ex.: Receita Federal")
                    org = gr.Textbox(label="Organização imitada (opcional)")
                    with gr.Row():
                        mode = gr.Dropdown(["PASSIVE", "SAFE_ENRICHMENT", "AUTHORIZED_ACTIVE"], value="PASSIVE", label="Modo")
                        budget = gr.Dropdown(["free", "balanced", "extended"], value="balanced", label="Profundidade",
                                             info="prazo da coleta: 45 s / 90 s / 180 s")
                    memory_enabled = gr.Checkbox(value=True, label="Usar Campaign Memory")
                    memory_path = gr.Textbox(label="Arquivo da memória (opcional)")
                ai_mode = gr.Dropdown(["OFF", "GLINER_ONLY", "GLINER_QWEN", "AUTO"], value="OFF", label="IA (modelos)",
                                      info="OFF ainda extrai com regras. GLiNER/Qwen acrescentam entidades e análise.")
                run = gr.Button("Executar investigação", variant="primary")
                demo = gr.Button("Carregar caso de demonstração (offline)")
                gr.Markdown("PASSIVE · balanced é o recomendado. E-mail e telefone são IOCs já observados: nenhuma busca de dados privados.")
                with gr.Accordion("Diagnóstico do ambiente", open=False):
                    gr.Markdown("Testa Python, dependências, pastas e a rede até cada fonte. Rode se uma busca não funcionar.")
                    diag_btn = gr.Button("Rodar diagnóstico")
                    diag_out = gr.HTML()
            with gr.Column(scale=2):
                summary = gr.HTML("<div class='ti-card ti-empty'><b>Aguardando investigação.</b><br>Preencha o alvo à esquerda ou carregue o caso de demonstração.</div>")
                with gr.Tabs():
                    with gr.Tab("Grafo"):
                        graph = gr.HTML()
                    with gr.Tab("IOCs"):
                        ioc_table = gr.Dataframe(interactive=False, wrap=True)
                    with gr.Tab("Isca e IA"):
                        lure_view = gr.HTML()
                        edges_table = gr.Dataframe(interactive=False, wrap=True, label="Ligações propostas pela IA (derivadas)")
                        ai_table = gr.Dataframe(interactive=False, wrap=True, label="Entidades GLiNER (bruto)")
                        ai_json = gr.JSON(label="Análise Qwen (validada contra o Evidence Ledger)")
                    with gr.Tab("Dados"):
                        rel_table = gr.Dataframe(interactive=False, wrap=True, label="Relações coletadas")
                        ev_table = gr.Dataframe(interactive=False, wrap=True, label="Evidence Ledger")
                        source_table = gr.Dataframe(interactive=False, wrap=True, label="Saúde das fontes")
                    with gr.Tab("Linha do tempo"):
                        timeline = gr.Markdown()
                    with gr.Tab("Campanha"):
                        gr.Markdown("**Lotes de registro:** domínios criados em sequência, no mesmo registrar e nameservers (indício de operação comum, não prova).")
                        batches_table = gr.Dataframe(interactive=False, wrap=True, label="Lotes de registro")
                        lures_table = gr.Dataframe(interactive=False, wrap=True, label="Iscas parecidas em casos anteriores (Campaign Memory)")
                    with gr.Tab("Memória"):
                        related_table = gr.Dataframe(interactive=False, wrap=True, label="Casos relacionados")
                        prevalence_table = gr.Dataframe(interactive=False, wrap=True, label="Prevalência / raridade")
                    with gr.Tab("Exportar"):
                        gr.Markdown("**STIX 2.1** (Indicators + Campaign), **MISP** e **Sigma** prontos para o seu TIP/SIEM.")
                        cti_files = gr.File(label="STIX · MISP · Sigma", file_count="multiple")
                        with gr.Accordion("Relatório HTML e pacote completo (ZIP)", open=False):
                            report_file = gr.File(label="Relatório HTML")
                            package_file = gr.File(label="Pacote completo ZIP")
        outs = [summary, graph, ioc_table, lure_view, edges_table, ai_table, ai_json, rel_table, ev_table, timeline, source_table,
                related_table, prevalence_table, batches_table, lures_table, cti_files, report_file, package_file]
        assert len(outs) == N_OUTPUTS
        run.click(execute, inputs=[target, target_type, case_id, analyst, brand, org, mode, budget, ai_mode, memory_enabled, memory_path], outputs=outs)
        demo.click(load_demo, outputs=[target, target_type, *outs])
        diag_btn.click(diagnose, outputs=[diag_out])
    app.launch_style = {} if legacy else style
    return app


def _allowed():
    return [str(default_base()), str(Path.home() / ".tropeiro")]


def _free_port(start: int = 7860, tries: int = 40) -> int:
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"nenhuma porta livre entre {start} e {start + tries - 1}")


def launch_local(server_port: int | None = None, share: bool = False, open_browser: bool = True):
    """Abre o Workbench no navegador local e bloqueia até Ctrl+C. Sem porta: usa a primeira livre a partir de 7860."""
    port = server_port or _free_port()
    app = build_app()
    print(f"Tropeiro Workbench: http://127.0.0.1:{port}  (Ctrl+C para encerrar)", flush=True)
    app.queue().launch(server_name="127.0.0.1", server_port=port, share=share, inbrowser=open_browser, show_error=True,
                       allowed_paths=_allowed(), **app.launch_style)


def launch_colab_frontend(server_port: int = 7860, inline: bool = True):
    """No Colab, deixa o Gradio decidir o compartilhamento (precisa de URL pública para exibir a interface)."""
    app = build_app()
    app.queue().launch(server_name="0.0.0.0", server_port=server_port, share=None, inline=inline, prevent_thread_lock=True, show_error=True,
                       allowed_paths=_allowed(), **app.launch_style)
    return app

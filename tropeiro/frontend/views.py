"""Renderizadores HTML/SVG puros (sem Gradio, sem rede): testáveis e reutilizáveis em relatórios."""
from __future__ import annotations
import html, math
from typing import Any, Dict, Iterable, List, Mapping
import networkx as nx

NODE_COLORS={'domain':'#E8A33D','ip':'#4FB3BF','org':'#9B8CFF','brand':'#FF7A6B','url':'#C9CED6',
             'email':'#7DD3A8','phone':'#7DD3A8','other':'#6B7280'}
METHOD_LABEL={'rule':'REGRA','gliner':'GLiNER'}

def _e(v): return html.escape(str(v),quote=True)

def _kind(label,known_types):
    return known_types.get(label,'other')

STATUS_LABEL={"OK":"✓ OK","UNAVAILABLE":"✗ indisponível","TIMEOUT":"⏱ prazo","SKIPPED_MISSING_SECRET":"– sem chave","SKIPPED_MODE":"– outro modo",
              "SKIPPED_BUDGET":"– profundidade","NOT_NEEDED":"– n/a"}

def kpi_html(summary: Mapping[str,Any], hybrid: List[Mapping[str,Any]], ai_edges: List[Mapping[str,Any]]) -> str:
    cards=[(summary.get('evidence',0),'evidências'),(summary.get('relationships',0),'relações'),
           (len(hybrid),'entidades extraídas'),(len(ai_edges),'ligações propostas (IA)'),
           (summary.get('sources_ok',0),'fontes OK'),(summary.get('memory_matches',0),'casos relacionados')]
    items=''.join(f"<div class='ti-kpi'><b>{_e(n)}</b><span>{_e(l)}</span></div>" for n,l in cards)
    notes=[f"Concluído em {summary.get('elapsed_s','?')} s (prazo {summary.get('deadline_s','?')} s)"]
    if summary.get('sources_failed'): notes.append(f"{summary['sources_failed']} fonte(s) indisponível(is): veja Dados → Saúde das fontes")
    if summary.get('sources_skipped'): notes.append(f"{summary['sources_skipped']} pulada(s) por modo, chave ou tipo de alvo")
    if summary.get('context_only'): notes.append(f"{summary['context_only']} IOC(s) de plataformas legítimas ficaram só como contexto")
    return (f"<div class='ti-card ti-summary'><div class='ti-eyebrow'>INVESTIGAÇÃO CONCLUÍDA · {_e(summary.get('case_id',''))} · {_e(summary.get('input_type',''))}</div>"
            f"<h2>{_e(str(summary.get('target',''))[:90])}</h2><div class='ti-kpis'>{items}</div>"
            f"<p class='ti-note'>{_e(' · '.join(notes))}</p><p class='ti-note'>{_e(summary.get('ai',''))}</p></div>")

def progress_html(elapsed: float, deadline: float, rows: List[Mapping[str,Any]], planned: int=0) -> str:
    pct=min(100,int(100*elapsed/max(deadline,1)))
    done=''.join(f"<li class='ti-st-{_e(r.get('status','')).lower()}'><b>{_e(STATUS_LABEL.get(r.get('status',''),r.get('status','')))}</b> "
                 f"{_e(r.get('source',''))} <span class='ti-note'>{_e(r.get('subject',''))} · {_e(r.get('seconds',0))} s"
                 f"{' · '+_e(r['error']) if r.get('error') else ''}</span></li>" for r in rows[-14:])
    total=f" de {planned}" if planned else ""
    return (f"<div class='ti-card ti-summary'><div class='ti-eyebrow'>COLETANDO EM PARALELO · {elapsed:.0f}s de no máximo {deadline:.0f}s</div>"
            f"<h2>{len([r for r in rows if r.get('status') in ('OK','UNAVAILABLE','TIMEOUT')])}{_e(total)} consultas concluídas</h2><div class='ti-bar' style='width:100%'><i style='width:{pct}%'></i></div>"
            f"<ul class='ti-src'>{done}</ul><p class='ti-note'>Uma fonte lenta não trava a busca: ao fim do prazo o resultado sai parcial.</p></div>")

def error_html(message: str) -> str:
    return (f"<div class='ti-card ti-summary ti-error'><div class='ti-eyebrow'>A BUSCA NÃO CONCLUIU</div><h2>{_e(message[:300])}</h2>"
            "<p class='ti-note'>Abra <b>Diagnóstico do ambiente</b> (abaixo, no painel esquerdo) ou rode <code>tropeiro doctor</code> no terminal. "
            "Para repetir sem interface: <code>tropeiro search SEU_ALVO</code>.</p></div>")

def diagnostics_html(checks) -> str:
    icon={"OK":"✓","WARN":"⚠","FAIL":"✗"}
    rows=''.join(f"<tr class='ti-dg-{_e(c.status).lower()}'><td>{icon[c.status]}</td><td>{_e(c.name)}</td><td>{_e(c.detail)}</td>"
                 f"<td class='ti-note'>{_e(c.hint) if c.status!='OK' else ''}</td></tr>" for c in checks)
    from ..doctor import verdict
    return (f"<div class='ti-card' style='padding:14px'><div class='ti-eyebrow'>DIAGNÓSTICO · {_e(verdict(checks))}</div>"
            f"<table class='ti-table'><tbody>{rows}</tbody></table></div>")

def source_rows(sources: Iterable[Mapping[str,Any]]) -> List[Dict[str,Any]]:
    order={"UNAVAILABLE":0,"TIMEOUT":1,"OK":2}
    return [{"fonte":r.get("source"),"assunto":r.get("subject"),"estado":STATUS_LABEL.get(r.get("status"),r.get("status")),
             "itens":r.get("items"),"segundos":r.get("seconds"),"observação":r.get("error")}
            for r in sorted(sources,key=lambda r:(order.get(r.get("status"),3),str(r.get("source"))))]

def graph_svg(rel_rows: Iterable[Mapping[str,Any]], ai_edges: Iterable[Mapping[str,Any]]=(), entities: Iterable[Mapping[str,Any]]=(),
              width: int=960, height: int=430, max_nodes: int=70) -> str:
    """Grafo de relações. Linha contínua = evidência coletada; tracejada = ligação proposta pela IA (derivada)."""
    types={}
    for e in entities: types[e['value']]=e.get('type','other')
    g=nx.Graph()
    for r in rel_rows:
        a,b=r.get('from'),r.get('to')
        if not a or not b or a==b: continue
        types.setdefault(a,'domain'); g.add_edge(a,b,derived=False,label=r.get('relationship',''))
    for r in ai_edges:
        if r.get('src') and r.get('dst') and r['src']!=r['dst']: g.add_edge(r['src'],r['dst'],derived=True,label=r.get('relation',''))
    if g.number_of_nodes()==0:
        return "<div class='ti-card ti-empty'>Sem relações para desenhar ainda.</div>"
    if g.number_of_nodes()>max_nodes:   # mantém os mais conectados
        keep=sorted(g.degree,key=lambda x:-x[1])[:max_nodes]; g=g.subgraph([n for n,_ in keep]).copy()
    pos=nx.spring_layout(g,seed=7,k=1.4/math.sqrt(max(1,g.number_of_nodes())),iterations=120)
    pad=95
    xs=[p[0] for p in pos.values()]; ys=[p[1] for p in pos.values()]
    def sx(x): return pad+(x-min(xs))/(max(xs)-min(xs) or 1)*(width-2*pad)
    def sy(y): return pad+(y-min(ys))/(max(ys)-min(ys) or 1)*(height-2*pad)
    parts=[f"<svg viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Grafo de relações' class='ti-graph'>"]
    for a,b,d in g.edges(data=True):
        dash=" stroke-dasharray='6 5'" if d.get('derived') else ''
        col='#9B8CFF' if d.get('derived') else '#4B5260'
        parts.append(f"<line x1='{sx(pos[a][0]):.1f}' y1='{sy(pos[a][1]):.1f}' x2='{sx(pos[b][0]):.1f}' y2='{sy(pos[b][1]):.1f}' stroke='{col}' stroke-width='1.4'{dash}><title>{_e(d.get('label',''))}</title></line>")
    for n in g.nodes:
        k=_kind(n,types); r=7+min(9,g.degree[n]*1.2)
        x,y=sx(pos[n][0]),sy(pos[n][1])
        parts.append(f"<g><circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' fill='{NODE_COLORS.get(k,NODE_COLORS['other'])}' stroke='#0B0D10' stroke-width='2'><title>{_e(n)} ({_e(k)})</title></circle>"
                     f"<text x='{x:.1f}' y='{y+r+13:.1f}' text-anchor='middle' font-size='11' fill='#C9CED6'>{_e(n if len(n)<=24 else n[:23]+'…')}</text></g>")
    parts.append('</svg>')
    legend=''.join(f"<span class='ti-dot' style='--c:{c}'>{_e(k)}</span>" for k,c in NODE_COLORS.items() if k!='other')
    legend+="<span class='ti-dash'>— evidência</span><span class='ti-dash ti-dash-ai'>- - ligação proposta (IA)</span>"
    return f"<div class='ti-card ti-graph-wrap'>{''.join(parts)}<div class='ti-legend'>{legend}</div></div>"

def lure_html(lures: List[Mapping[str,Any]], entities: List[Mapping[str,Any]]) -> str:
    chips=''.join(f"<span class='ti-chip'><b>{_e(l['brand'])}</b> · {_e(l['theme'])}</span>" for l in lures) or "<span class='ti-note'>Nenhuma isca brasileira conhecida detectada.</span>"
    rows=''
    for e in entities[:60]:
        meth=''.join(f"<span class='ti-badge ti-{_e(m)}'>{_e(METHOD_LABEL.get(m,m))}</span>" for m in e.get('methods',[]))
        if e.get('legit_platform'): meth+="<span class='ti-badge ti-legit'>PLATAFORMA LEGÍTIMA</span>"
        pct=int(float(e.get('score',0))*100)
        rows+=(f"<tr><td><span class='ti-type'>{_e(e.get('type'))}</span></td><td class='ti-mono'>{_e(e.get('value'))}</td><td>{meth}</td>"
               f"<td><div class='ti-bar'><i style='width:{pct}%'></i></div><span class='ti-note'>{pct}% · {_e(e.get('confidence',''))}</span></td></tr>")
    table=(f"<table class='ti-table'><thead><tr><th>Tipo</th><th>Valor</th><th>Método</th><th>Confiança</th></tr></thead><tbody>{rows}</tbody></table>"
           if rows else "<p class='ti-note'>Nenhuma entidade extraída.</p>")
    return (f"<div class='ti-card' style='padding:18px'><div class='ti-eyebrow'>MARCA / TEMA DA ISCA</div><div class='ti-chips'>{chips}</div>"
            f"<div class='ti-eyebrow' style='margin-top:18px'>ENTIDADES (derivadas · requerem confirmação do analista)</div>{table}</div>")

IOC_COLS=[('ioc','IOC'),('ioc_type','tipo'),('decision','decisão'),('confidence_band','confiança'),
          ('false_positive_risk','risco de FP'),('evidence_count','evidências'),('independent_sources','fontes indep.'),('expiration_guidance','revalidar')]

def ioc_rows(decisions: Iterable[Mapping[str,Any]]) -> List[Dict[str,Any]]:
    """Visão enxuta das decisões (a tabela completa continua no case.json)."""
    return [{label:d.get(key) for key,label in IOC_COLS} for d in decisions]

def edges_rows(ai_edges: Iterable[Mapping[str,Any]]) -> List[Dict[str,Any]]:
    return [{'de':e['src'],'relação':e['relation'],'para':e['dst'],'score':e['score'],'extração':'+'.join(e.get('extraction',[]))} for e in ai_edges]

HERO="""<div id='ti-hero'><div class='ti-eyebrow'>TROPEIRO · PHISHING CAMPAIGN INTELLIGENCE</div>
<h1>Investigation <span>Workbench</span></h1>
<p>Cole um alvo ou o texto da isca. O Tropeiro coleta passivamente, extrai entidades (regras + GLiNER), liga o que é discriminante e entrega evidência rastreável — nunca prova de identidade.</p></div>"""

APP_CSS="""
:root{--bg:#0B0D10;--panel:#12151A;--line:#252A32;--muted:#8E96A3;--ink:#F2F4F7;--acc:#E8A33D;--ai:#9B8CFF}
.gradio-container{max-width:1480px!important;margin:0 auto!important;background:var(--bg)!important;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Inter,sans-serif!important}
footer{display:none!important}
#ti-hero{padding:30px 6px 10px}
#ti-hero h1{font-size:46px;line-height:1.02;margin:6px 0 10px;letter-spacing:-.045em;color:var(--ink)}
#ti-hero h1 span{color:var(--acc)}
#ti-hero p{color:var(--muted);max-width:820px;font-size:15px;line-height:1.55}
.ti-eyebrow{font:600 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.ti-card{border:1px solid var(--line)!important;border-radius:14px!important;background:var(--panel)!important}
.ti-summary{padding:20px}.ti-summary h2{margin:6px 0 16px;font-size:24px;letter-spacing:-.02em;color:var(--ink);word-break:break-all}
.ti-kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.ti-kpi{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:#0F1217}
.ti-kpi{min-width:0}@media(max-width:900px){.ti-kpis{grid-template-columns:repeat(2,1fr)}}
.ti-card h3{padding:14px 16px 0}
.ti-kpi b{display:block;font-size:28px;letter-spacing:-.03em;color:var(--acc)}.ti-kpi span{font-size:12px;color:var(--muted)}
.ti-note{color:var(--muted);font-size:12px}.ti-empty{padding:28px;color:var(--muted)}
.ti-graph{width:100%;height:auto;display:block}.ti-graph-wrap{padding:10px}
.ti-legend{display:flex;gap:16px;flex-wrap:wrap;padding:8px 12px 4px;font-size:12px;color:var(--muted)}
.ti-dot:before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--c);margin-right:6px}
.ti-dash-ai{color:var(--ai)}
.ti-chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.ti-chip{border:1px solid var(--acc);color:var(--acc);padding:5px 12px;border-radius:999px;font-size:13px}
.ti-table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}
.ti-table th{text-align:left;color:var(--muted);font-weight:500;padding:6px 8px;border-bottom:1px solid var(--line)}
.ti-table td{padding:8px;border-bottom:1px solid #1B1F26;vertical-align:middle}
.ti-mono{font-family:ui-monospace,Menlo,monospace;color:var(--ink);word-break:break-all}
.ti-type{font:600 11px ui-monospace,monospace;color:var(--muted);text-transform:uppercase}
.ti-badge{font:700 10px ui-monospace,monospace;padding:3px 7px;border-radius:6px;margin-right:4px;letter-spacing:.06em}
.ti-rule{background:#E8A33D22;color:var(--acc)}.ti-gliner{background:#9B8CFF22;color:var(--ai)}
.ti-error{border-color:#FF7A6B!important}.ti-error h2{color:#FF7A6B}
.ti-src{list-style:none;padding:0;margin:12px 0 4px;font-size:13px;color:#C9CED6}.ti-src li{padding:3px 0}
.ti-dg-fail td{color:#FF7A6B}.ti-dg-warn td{color:#E8A33D}
.ti-legit{background:#4FB3BF22;color:#4FB3BF}
.ti-bar{height:6px;background:#1B1F26;border-radius:4px;width:120px;margin-bottom:3px}.ti-bar i{display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,var(--ai),var(--acc))}
"""

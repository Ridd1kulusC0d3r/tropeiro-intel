import html, json, webbrowser
from pathlib import Path
from datetime import datetime, timezone
from .brand import logo_svg, BRAND_NAME, BRAND_TAGLINE

def esc(v): return html.escape("" if v is None else str(v))
def _rows(data):
    if data is None: return []
    if isinstance(data,list): return [x for x in data if isinstance(x,dict)]
    if isinstance(data,dict): return [{"key":k,"value":v} for k,v in data.items()]
    return []
def _table(rows, columns=None, table_id="", empty="Sem dados para esta seção."):
    rows=_rows(rows)
    if not rows: return f'<div class="empty">{esc(empty)}</div>'
    columns=columns or list(dict.fromkeys(k for r in rows for k in r.keys()))
    head=''.join(f'<th>{esc(c.replace("_"," ").title())}</th>' for c in columns)
    body=[]
    for r in rows:
        cells=[]
        for c in columns:
            v=r.get(c,'')
            if isinstance(v,(list,dict)): v=json.dumps(v,ensure_ascii=False,default=str)
            cells.append(f'<td>{esc(v)}</td>')
        body.append('<tr>'+''.join(cells)+'</tr>')
    return f'<div class="table-wrap"><table id="{esc(table_id)}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
def _metric(label,value,note=''): return f'<div class="metric"><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(note)}</small></div>'
def _pill(text,tone='neutral'): return f'<span class="pill {esc(tone)}">{esc(text)}</span>'
def _tone(band): return {'HIGH':'danger','MODERATE':'warn','LOW':'info'}.get(str(band or '').upper(),'neutral')
def _bar(value):
    try:v=max(0,min(1,float(value)))
    except Exception:v=0
    return f'<div class="bar"><i style="width:{v*100:.1f}%"></i></div>'
def _confidence_cards(confidence):
    out=[]
    for name,v in (confidence or {}).items():
        score=float((v.get('score',0) if isinstance(v,dict) else v) or 0); band=v.get('band','') if isinstance(v,dict) else ''
        out.append('<div class="confidence-card">'+f'<div><span>{esc(name.replace("_"," ").title())}</span>{_pill(band,_tone(band))}</div><strong>{score:.2f}</strong>{_bar(score)}</div>')
    return ''.join(out) or '<div class="empty">Sem matriz de confiança.</div>'
def _actions(actions):
    rows=[{'priority':a.get('priority'),'action':a.get('action'),'target':a.get('target'),'owner':a.get('owner'),'why':a.get('why')} for a in (actions or [])]
    return _table(rows,['priority','action','target','owner','why'],'actions-table')
def _ioc_decisions(rows):
    cleaned=[{'ioc':x.get('ioc'),'type':x.get('ioc_type'),'confidence':x.get('confidence'),'actionability':x.get('actionability'),'active':x.get('active_now'),'fp_risk':x.get('false_positive_risk'),'block':x.get('block_recommended'),'hunt':x.get('hunt_recommended'),'takedown':x.get('takedown_candidate')} for x in (rows or [])]
    return _table(cleaned,['ioc','type','confidence','actionability','active','fp_risk','block','hunt','takedown'],'ioc-table')
def _simple_list(items,limit=15):
    if not items:return '<div class="empty">Sem dados.</div>'
    return '<ul class="clean-list">'+''.join(f'<li>{esc(x)}</li>' for x in items[:limit])+'</ul>'

def build_report(data, output_path, title=None):
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    meta=data.get('meta',{}); brief=data.get('executive_brief',{}); assessment=brief.get('executive_assessment',data.get('executive_assessment',{}))
    actions=data.get('action_matrix',brief.get('immediate_actions',[])); iocs=data.get('ioc_decisions',[]); gaps=data.get('collection_gaps',brief.get('what_we_dont_know',[])); pivots=data.get('next_best_pivots',brief.get('next_best_pivots',[]))
    confidence=data.get('confidence',brief.get('confidence',{})); victimology=data.get('victimology',brief.get('victimology',{})); objectives=data.get('objectives',brief.get('objectives',{})); lifecycle=data.get('lifecycle',brief.get('campaign_state',{}))
    attribution=data.get('attribution_assessments',[]); clusters=data.get('campaign_clusters',[]); evidence=data.get('evidence_ledger',[]); source_status=data.get('source_status',[]); detection=data.get('detection_package',{}); ownership=data.get('ownership',{})
    case_id=meta.get('case_id') or data.get('case_id') or 'CASE'; analyst=meta.get('analyst') or 'não informado'; generated=meta.get('generated_at') or datetime.now(timezone.utc).isoformat(); title=title or f'{BRAND_NAME} · {case_id}'
    block_n=sum(1 for x in iocs if x.get('block_recommended')); hunt_n=sum(1 for x in iocs if x.get('hunt_recommended')); p1_n=sum(1 for x in actions if x.get('priority')=='P1'); high_attr=sum(1 for x in attribution if str(x.get('common_operator_confidence','')).upper()=='HIGH')
    nav=[('overview','Overview'),('actions','Ações'),('iocs','IOCs'),('campaign','Campanha'),('attribution','Atribuição'),('gaps','Gaps & Pivôs'),('detection','Detecção'),('evidence','Evidências'),('sources','Fontes'),('exports','Export Center')]
    nav_html=''.join(f'<a href="#{a}">{b}</a>' for a,b in nav)
    embed={'executive_brief':brief,'action_matrix':actions,'ioc_decisions':iocs,'collection_gaps':gaps,'next_best_pivots':pivots,'confidence':confidence,'victimology':victimology,'objectives':objectives,'lifecycle':lifecycle,'attribution_assessments':attribution,'campaign_clusters':clusters,'evidence_ledger':evidence,'source_status':source_status,'ownership':ownership,'detection_package':detection}
    embedded=json.dumps(embed,ensure_ascii=False,default=str).replace('</','<\\/')
    judgment=assessment.get('judgment','') if isinstance(assessment,dict) else str(assessment); implication=assessment.get('implication','') if isinstance(assessment,dict) else ''
    ownership_rows=[{'domain':k,**(v if isinstance(v,dict) else {'value':v})} for k,v in ownership.items()]; block_domains=(detection.get('blocklist') or {}).get('domains',[])
    css="""
:root{--bg:#f6f7f8;--panel:#fff;--ink:#111315;--muted:#68707a;--line:#dfe3e7;--soft:#eef1f3;--radius:16px;--shadow:0 8px 28px rgba(0,0,0,.06)}
[data-theme=dark]{--bg:#0d0f11;--panel:#131619;--ink:#f3f4f5;--muted:#969da5;--line:#292e33;--soft:#1b1f23;--shadow:none}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.shell{max-width:1540px;margin:auto;padding:0 24px 56px}
.topbar{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);margin:0 -24px;padding:12px 24px;display:flex;align-items:center;gap:18px}.brand{display:flex;align-items:center;gap:12px;min-width:max-content}.brand strong{font-size:15px}.brand small{display:block;color:var(--muted);font-size:11px}.nav{display:flex;gap:4px;overflow:auto;white-space:nowrap;flex:1}.nav a{text-decoration:none;color:var(--muted);padding:7px 9px;border-radius:8px;font-size:12px}.nav a:hover{background:var(--soft);color:var(--ink)}.toolbar{display:flex;gap:8px}.btn{border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:8px 11px;border-radius:9px;cursor:pointer}
header.hero{padding:56px 0 28px;display:grid;grid-template-columns:1.5fr 1fr;gap:28px;align-items:end}.eyebrow{font:600 11px/1.2 ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}h1{font-size:44px;line-height:1.06;margin:10px 0 14px;letter-spacing:-.04em}.lede{font-size:18px;line-height:1.55;color:var(--muted);max-width:850px}.hero-meta{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.metric,.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}.metric{padding:15px}.metric span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}.metric strong{font-size:25px;display:block;margin-top:7px}.metric small{color:var(--muted)}section{scroll-margin-top:80px;margin-top:32px}.section-head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:12px}h2{font-size:23px;margin:0}.section-head p{color:var(--muted);margin:0;max-width:680px}.grid{display:grid;gap:12px}.grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}.card{padding:18px}.card h3{margin:0 0 12px;font-size:15px}.judgment{font-size:22px;line-height:1.45}.muted{color:var(--muted)}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;font-size:11px;font-weight:650}.pill.danger{background:var(--ink);color:var(--bg);border-color:var(--ink)}.pill.warn,.pill.info{background:var(--soft)}.confidence-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.confidence-card{padding:14px;border:1px solid var(--line);border-radius:12px}.confidence-card>div:first-child{display:flex;justify-content:space-between;gap:10px}.confidence-card strong{font-size:26px}.bar{height:5px;background:var(--soft);border-radius:99px;overflow:hidden;margin-top:9px}.bar i{display:block;height:100%;background:currentColor}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px}table{width:100%;border-collapse:collapse;min-width:720px}th{position:sticky;top:0;background:var(--soft);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}tbody tr:hover{background:var(--soft)}.empty{padding:22px;color:var(--muted);border:1px dashed var(--line);border-radius:12px}.clean-list{margin:0;padding-left:18px}.clean-list li{margin:7px 0}.code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;white-space:pre-wrap;word-break:break-word;background:var(--soft);border-radius:12px;padding:14px;max-height:430px;overflow:auto}.filter{width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink);margin-bottom:9px}.export-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.export-item{padding:14px;border:1px solid var(--line);border-radius:12px}.export-item button{width:100%;margin-top:10px}footer{margin-top:50px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media(max-width:980px){header.hero,.grid-2,.confidence-grid,.export-grid{grid-template-columns:1fr}h1{font-size:34px}.hero-meta{grid-template-columns:1fr 1fr}}@media print{.topbar,.filter,.export-actions{display:none!important}body{background:#fff;color:#000}.shell{max-width:none;padding:0}.card,.metric{box-shadow:none;break-inside:avoid}.table-wrap{overflow:visible}table{min-width:0;font-size:10px}}
"""
    doc=f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title><style>{css}</style></head><body><div class='shell'>
<div class='topbar'><div class='brand'>{logo_svg(34)}<div><strong>{BRAND_NAME}</strong><small>{BRAND_TAGLINE}</small></div></div><nav class='nav'>{nav_html}</nav><div class='toolbar'><button class='btn' onclick='toggleTheme()'>◐ Tema</button><button class='btn' onclick='window.print()'>↧ PDF</button></div></div>
<header class='hero'><div><div class='eyebrow'>Intelligence Report · {esc(case_id)}</div><h1>{esc(judgment or title)}</h1><div class='lede'>{esc(implication)}</div><p class='muted'>Analista: {esc(analyst)} · Gerado em {esc(generated)}</p></div><div class='hero-meta'>{_metric('P1 Actions',p1_n,'ações prioritárias')}{_metric('Block Ready',block_n,'IOCs')}{_metric('Hunt Ready',hunt_n,'IOCs')}{_metric('High Attribution',high_attr,'relações')}</div></header>
<section id='overview'><div class='section-head'><div><div class='eyebrow'>01 · Assessment</div><h2>Visão executiva</h2></div><p>Estado da campanha, objetivo, vítima e confiança primeiro.</p></div><div class='grid grid-2'><div class='card'><h3>Campaign State</h3><div class='judgment'>{esc(lifecycle.get('stage','UNKNOWN'))}</div><p class='muted'>First seen: {esc(lifecycle.get('first_seen','?'))}<br>Last seen: {esc(lifecycle.get('last_seen','?'))}</p></div><div class='card'><h3>Objective</h3><div class='judgment'>{esc(objectives.get('primary','unknown'))}</div><p class='muted'>Confiança: {esc(objectives.get('confidence',''))}</p></div><div class='card'><h3>Victimology</h3>{_table([victimology],table_id='victimology-table')}</div><div class='card'><h3>Confidence Matrix</h3><div class='confidence-grid'>{_confidence_cards(confidence)}</div></div></div></section>
<section id='actions'><div class='section-head'><div><div class='eyebrow'>02 · Decision</div><h2>Action Matrix</h2></div><p>Prioridade, dono e justificativa.</p></div><input class='filter' placeholder='Filtrar ações…' oninput=\"filterTable('actions-table',this.value)\"><div class='card'>{_actions(actions)}</div></section>
<section id='iocs'><div class='section-head'><div><div class='eyebrow'>03 · Enforcement</div><h2>IOC Decision Objects</h2></div><p>Confidence, actionability e falso positivo separados.</p></div><input class='filter' placeholder='Filtrar IOC…' oninput=\"filterTable('ioc-table',this.value)\"><div class='card'>{_ioc_decisions(iocs)}</div></section>
<section id='campaign'><div class='section-head'><div><div class='eyebrow'>04 · Campaign</div><h2>Campanha e ownership</h2></div><p>Clusters e contexto de controle/infraestrutura.</p></div><div class='grid grid-2'><div class='card'><h3>Campaign clusters</h3>{_table(clusters,table_id='clusters-table')}</div><div class='card'><h3>Ownership summary</h3>{_table(ownership_rows,table_id='ownership-table')}</div></div></section>
<section id='attribution'><div class='section-head'><div><div class='eyebrow'>05 · Attribution</div><h2>Operator correlation</h2></div><p>Infraestrutura, operador e identidade permanecem dimensões separadas.</p></div><div class='card'>{_table(attribution,table_id='attr-table')}</div></section>
<section id='gaps'><div class='section-head'><div><div class='eyebrow'>06 · Collection</div><h2>Gaps & Next Best Pivots</h2></div><p>O que falta saber e onde vale gastar o próximo minuto.</p></div><div class='grid grid-2'><div class='card'><h3>Collection gaps</h3>{_table(gaps,table_id='gaps-table')}</div><div class='card'><h3>Pivot ranking</h3>{_table(pivots[:50],table_id='pivot-table')}</div></div></section>
<section id='detection'><div class='section-head'><div><div class='eyebrow'>07 · Defense</div><h2>Detection Engineering</h2></div><p>Hunting e controles candidatos.</p></div><div class='grid grid-2'><div class='card'><h3>Package</h3><div class='code'>{esc(json.dumps(detection,ensure_ascii=False,indent=2,default=str))}</div></div><div class='card'><h3>Blocklist</h3>{_simple_list(block_domains)}</div></div></section>
<section id='evidence'><div class='section-head'><div><div class='eyebrow'>08 · Provenance</div><h2>Evidence Ledger</h2></div><p>Proveniência para reproduzir, contestar ou sustentar o julgamento.</p></div><input class='filter' placeholder='Filtrar evidência…' oninput=\"filterTable('evidence-table',this.value)\"><div class='card'>{_table(evidence,table_id='evidence-table')}</div></section>
<section id='sources'><div class='section-head'><div><div class='eyebrow'>09 · Coverage</div><h2>Saúde das fontes</h2></div><p>Falha de coleta aparece explicitamente.</p></div><div class='card'>{_table(source_status,table_id='sources-table')}</div></section>
<section id='exports'><div class='section-head'><div><div class='eyebrow'>10 · Output</div><h2>Export Center</h2></div><p>Exporte apenas o que precisa.</p></div><div class='export-grid export-actions'>
<div class='export-item'><strong>Executive brief</strong><p class='muted'>Resumo para decisão.</p><button class='btn' onclick=\"downloadJSON('executive_brief')\">JSON</button></div><div class='export-item'><strong>IOC decisions</strong><p class='muted'>Bloqueio/hunt/takedown.</p><button class='btn' onclick=\"downloadCSV('ioc_decisions')\">CSV</button></div><div class='export-item'><strong>Actions</strong><p class='muted'>Matriz operacional.</p><button class='btn' onclick=\"downloadCSV('action_matrix')\">CSV</button></div><div class='export-item'><strong>Evidence</strong><p class='muted'>Ledger completo.</p><button class='btn' onclick=\"downloadCSV('evidence_ledger')\">CSV</button></div><div class='export-item'><strong>Attribution</strong><p class='muted'>Relações e confiança.</p><button class='btn' onclick=\"downloadCSV('attribution_assessments')\">CSV</button></div><div class='export-item'><strong>Gaps</strong><p class='muted'>Próximas coletas.</p><button class='btn' onclick=\"downloadCSV('collection_gaps')\">CSV</button></div><div class='export-item'><strong>Full case</strong><p class='muted'>Dados embutidos.</p><button class='btn' onclick='downloadAll()'>JSON</button></div><div class='export-item'><strong>PDF</strong><p class='muted'>Versão imprimível.</p><button class='btn' onclick='window.print()'>Print / PDF</button></div></div></section>
<footer>{logo_svg(24)} <strong>{BRAND_NAME}</strong> · Offline Intelligence Report · {esc(case_id)}<br>Julgamentos analíticos dependem das evidências disponíveis; atribuição de identidade exige evidência independente suficiente.</footer></div>
<script id='tropeiro-data' type='application/json'>{embedded}</script><script>
const D=JSON.parse(document.getElementById('tropeiro-data').textContent);function toggleTheme(){{document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'':'dark';}}function filterTable(id,q){{q=q.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none');}}function saveBlob(name,text,type){{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{{type}}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}}function downloadJSON(key){{saveBlob('{esc(case_id)}_'+key+'.json',JSON.stringify(D[key]??{{}},null,2),'application/json');}}function csvEscape(v){{v=(v===null||v===undefined)?'':(typeof v==='object'?JSON.stringify(v):String(v));return '\"'+v.replaceAll('\"','\"\"')+'\"';}}function toCSV(rows){{if(!Array.isArray(rows))rows=[rows];if(!rows.length)return '';const cols=[...new Set(rows.flatMap(x=>Object.keys(x||{{}})))];return cols.map(csvEscape).join(',')+'\\n'+rows.map(r=>cols.map(c=>csvEscape((r||{{}})[c])).join(',')).join('\\n');}}function downloadCSV(key){{saveBlob('{esc(case_id)}_'+key+'.csv',toCSV(D[key]??[]),'text/csv;charset=utf-8');}}function downloadAll(){{saveBlob('{esc(case_id)}_tropeiro_case.json',JSON.stringify(D,null,2),'application/json');}}
</script></body></html>"""
    output_path.write_text(doc,encoding='utf-8'); return output_path

def open_local_report(path):
    p=Path(path).resolve()
    try:webbrowser.open(p.as_uri()); return True
    except Exception:return False

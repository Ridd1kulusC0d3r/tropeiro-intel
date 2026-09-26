import html, math


def _e(v):return html.escape(str(v or ''))

def relationship_svg(graph,max_nodes=70,width=920,height=520):
    nodes=(graph or {}).get('nodes',[])[:max_nodes]
    ids=[str(x.get('id') or x.get('value')) for x in nodes]
    keep=set(ids)
    edges=[e for e in (graph or {}).get('edges',[]) if str(e.get('source')) in keep and str(e.get('target')) in keep][:180]
    if not nodes:return '<div class="empty">Sem grafo de relacionamento.</div>'
    cx,cy=width/2,height/2;radius=min(width,height)*.38
    pos={}
    for i,n in enumerate(nodes):
        a=2*math.pi*i/max(1,len(nodes));pos[ids[i]]=(cx+radius*math.cos(a),cy+radius*math.sin(a))
    lines=[]
    for e in edges:
        a,b=pos.get(str(e.get('source'))),pos.get(str(e.get('target')))
        if not a or not b:continue
        w=max(1,min(4,float(e.get('weight',.5) or .5)*3))
        lines.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="currentColor" stroke-opacity=".24" stroke-width="{w:.1f}"/>')
    dots=[]
    for i,n in enumerate(nodes):
        ident=ids[i];x,y=pos[ident];typ=_e(n.get('type') or n.get('node_type') or 'entity');label=_e(ident[:34])
        dots.append(f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="currentColor"><title>{_e(ident)} · {typ}</title></circle><text x="{x+10:.1f}" y="{y+4:.1f}" font-size="10" fill="currentColor">{label}</text></g>')
    return f'<div class="graph"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Relationship graph">{"".join(lines)}{"".join(dots)}</svg></div>'


def timeline_svg(rows,width=920,height=180):
    vals=[x for x in (rows or []) if x.get('observed_at') or x.get('timestamp')]
    if not vals:return '<div class="empty">Sem timeline.</div>'
    vals=vals[:120]
    pad=30;usable=width-pad*2
    dots=[]
    for i,r in enumerate(vals):
        x=pad+(usable*i/max(1,len(vals)-1));y=height/2+(18 if i%2 else -18)
        label=_e((r.get('entity') or r.get('value') or '')[:28]);ts=_e(r.get('observed_at') or r.get('timestamp'))
        dots.append(f'<line x1="{x:.1f}" y1="{height/2}" x2="{x:.1f}" y2="{y:.1f}" stroke="currentColor" stroke-opacity=".35"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="currentColor"><title>{ts} · {label}</title></circle>')
    return f'<div class="graph"><svg viewBox="0 0 {width} {height}"><line x1="{pad}" y1="{height/2}" x2="{width-pad}" y2="{height/2}" stroke="currentColor" stroke-opacity=".3"/>{"".join(dots)}</svg></div>'

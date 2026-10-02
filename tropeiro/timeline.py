def build_timeline(ledger_df):
    if ledger_df is None or ledger_df.empty: return []
    cols=[c for c in ['observed_at','entity','entity_type','source','value','evidence_id'] if c in ledger_df.columns]
    return ledger_df[cols].sort_values('observed_at').to_dict('records')

def timeline_summary(events):
    """Por entidade: primeira/última observação e fontes distintas. `events` = saída de build_timeline."""
    out={}
    for e in events or []:
        ent=e.get('entity'); t=e.get('observed_at')
        if not ent or not t: continue
        r=out.setdefault(ent,{'first_seen':t,'last_seen':t,'observations':0,'sources':set()})
        r['first_seen']=min(r['first_seen'],t); r['last_seen']=max(r['last_seen'],t)
        r['observations']+=1
        if e.get('source'): r['sources'].add(e['source'])
    return {k:{**v,'sources':sorted(v['sources'])} for k,v in sorted(out.items(),key=lambda kv:kv[1]['first_seen'])}

def timeline_markdown(events):
    """Linha do tempo em Markdown para colar em relatório."""
    lines=['| Primeira vez | Última vez | Entidade | Obs. | Fontes |','|---|---|---|---|---|']
    for ent,r in timeline_summary(events).items():
        lines.append(f"| {r['first_seen']} | {r['last_seen']} | `{ent}` | {r['observations']} | {', '.join(r['sources'])} |")
    return '\n'.join(lines)

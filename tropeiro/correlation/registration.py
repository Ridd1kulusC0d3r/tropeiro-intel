"""Lotes de registro: domínios criados juntos, no mesmo registrar/NS, costumam ser do mesmo operador."""
from datetime import datetime

def _ts(v):
    try: return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except ValueError: return None

def registration_batches(rows,window_seconds=600,min_size=2):
    """`rows`: [{'domain','created','registrar','nameservers'}] (campos de collectors.rdap.lookup).

    Agrupa por (registrar, nameservers) e depois por janela de tempo entre criações consecutivas.
    Devolve lotes com o motivo, para o analista julgar: é indício, não prova de operador único.
    """
    by_infra={}
    for r in rows:
        t=_ts(r.get('created'))
        if t is None: continue
        key=(str(r.get('registrar') or '').lower(),tuple(sorted(r.get('nameservers') or [])))
        by_infra.setdefault(key,[]).append((t,r['domain'],r.get('created')))
    out=[]
    for (registrar,ns),items in by_infra.items():
        items.sort(); batch=[items[0]]
        for it in items[1:]+[None]:
            if it is not None and it[0]-batch[-1][0]<=window_seconds: batch.append(it); continue
            if len(batch)>=min_size:
                out.append({'domains':[b[1] for b in batch],'first':batch[0][2],'last':batch[-1][2],
                            'registrar':registrar,'nameservers':list(ns),
                            'reason':f'{len(batch)} domínios criados em {int(batch[-1][0]-batch[0][0])}s com mesmo registrar/NS'})
            if it is not None: batch=[it]
    return out

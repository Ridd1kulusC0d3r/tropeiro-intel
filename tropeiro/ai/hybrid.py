"""Extração e correlação híbridas: regras determinísticas primeiro, GLiNER por cima, tudo marcado como derivado.

Princípios:
- o pipeline funciona sem modelo (regras BR + IOCs); o GLiNER só acrescenta entidades de contexto;
- entidade confirmada por regra E modelo ganha confiança; entidade só-modelo é validada (hostname/IP válidos);
- nada aqui escreve no Evidence Ledger: saídas são candidatos (`derived=True`, `analyst_confirmed=False`).
"""
from __future__ import annotations
import hashlib, ipaddress
from typing import Any, Dict, Iterable, List, Mapping, Optional
from rapidfuzz import fuzz
from ..utils import refang, valid_hostname, root_domain
from ..intelligence.br_lures import extract_lure_infra, detect_br_lures
from .core import extract_gliner_entities, DEFAULT_ENTITY_LABELS

# rótulo do GLiNER -> tipo canônico do Tropeiro
LABEL_MAP={'domain':'domain','url':'url','ip address':'ip','email address':'email','phone number':'phone',
           'organization':'org','brand':'brand','financial institution':'org','registrar':'registrar',
           'hosting provider':'hosting','malware family':'malware','campaign name':'campaign',
           'threat actor alias':'actor','payment method':'payment','tracking id':'tracking_id',
           'certificate name':'domain','asn':'asn','country':'country'}

def _eid(kind,value): return 'ai-'+hashlib.sha256(f'{kind}|{value}'.encode()).hexdigest()[:12]

def _valid(kind,value):
    if kind=='domain': return valid_hostname(value)
    if kind=='ip':
        try: return str(ipaddress.ip_address(value))
        except ValueError: return None
    if kind=='email': return value.lower() if '@' in value and valid_hostname(value.split('@')[-1]) else None
    if kind=='url': return value if value.lower().startswith(('http://','https://')) else None
    if kind=='phone':
        d=''.join(c for c in value if c.isdigit()); return d if 10<=len(d)<=13 else None
    return value.strip() or None

def extract_hybrid(text: str, gliner: Any=None, labels: Optional[List[str]]=None, threshold: float=.45, source: str='lure_text') -> List[Dict[str,Any]]:
    """Retorna entidades candidatas, ordenadas por confiança. `gliner`: GLiNERLocal | None (só regras)."""
    text=refang(text); found={}
    def put(kind,value,method,score,extra=None):
        v=_valid(kind,value)
        if not v: return
        key=(kind,v.casefold()); row=found.get(key)
        if row is None:
            row={'candidate_id':_eid(kind,v),'type':kind,'value':v,'methods':[],'score':0.0,'source_context':source,
                 'derived':True,'analyst_confirmed':False,**(extra or {})}
            found[key]=row
        if method not in row['methods']: row['methods'].append(method)
        row['score']=max(row['score'],score)
    for kind,vals in extract_lure_infra(text).items():
        for v in vals: put(kind,v,'rule',.9)
    for hit in detect_br_lures(text):
        put('brand',hit['brand'],'rule',.8,{'theme':hit['theme'],'matched':hit['matched']})
    if gliner is not None:
        items=[{'source':source,'text':text}]
        model=gliner.load() if hasattr(gliner,'load') else gliner
        for e in extract_gliner_entities(items,model,labels=labels or DEFAULT_ENTITY_LABELS,threshold=threshold):
            kind=LABEL_MAP.get(e['label'].lower(),e['label'].lower())
            put(kind,e['value'],'gliner',e['score'],{'span':[e.get('start'),e.get('end')]})
    for row in found.values():
        if len(row['methods'])>1: row['score']=round(min(.99,row['score']+.08),3)   # concordância regra+modelo
        else: row['score']=round(row['score'],3)
        row['confidence']='HIGH' if row['score']>=.85 else 'MODERATE' if row['score']>=.6 else 'LOW'
    return sorted(found.values(),key=lambda r:(-r['score'],r['type'],r['value']))

def correlate_entities(entities: Iterable[Mapping[str,Any]], known: Iterable[str], fuzzy: int=88) -> List[Dict[str,Any]]:
    """Liga candidatos a entidades já presentes no caso (`known`: domínios/IPs/e-mails/nomes do ledger).

    Relações propostas (todas `derived`): `same_value`, `same_root_domain`, `similar_name`.
    O `score` mistura a confiança da extração com a força da ligação.
    """
    known=[k for k in {str(x) for x in known} if k]; low={k.casefold():k for k in known}
    roots={}
    for k in known:
        if valid_hostname(k): roots.setdefault(root_domain(k),[]).append(k)
    edges=[]
    def add(ent,dst,rel,strength):
        edges.append({'src':ent['value'],'dst':dst,'relation':rel,'score':round(ent['score']*strength,3),
                      'strength':strength,'extraction':ent.get('methods',[]),'derived':True,'analyst_confirmed':False})
    for ent in entities:
        v=str(ent['value']); kind=ent['type']
        if v.casefold() in low:
            add(ent,low[v.casefold()],'same_value',1.0)
            if kind not in ('domain','url','email'): continue
        if kind in ('domain','url','email'):
            h=valid_hostname(v.split('@')[-1] if kind=='email' else v.split('//')[-1].split('/')[0])
            if h:
                for dst in roots.get(root_domain(h),[]):
                    if dst!=h: add(ent,dst,'same_root_domain',.7)
        elif kind in ('org','brand','registrar','hosting'):
            for k in known:
                r=fuzz.token_set_ratio(v.casefold(),k.casefold())
                if r>=fuzzy and not valid_hostname(k): add(ent,k,'similar_name',round(r/100,2))
    return sorted(edges,key=lambda e:-e['score'])

def lure_similarity(text: str, others: Mapping[str,str], threshold: int=70) -> List[Dict[str,Any]]:
    """Compara a isca com iscas de outros casos (`{case_id: texto}`). Útil para ligar campanhas sem IOC em comum."""
    t=refang(text).casefold(); out=[]
    for cid,o in others.items():
        r=fuzz.token_set_ratio(t,refang(o).casefold())
        if r>=threshold: out.append({'case_id':cid,'similarity':round(r/100,2),'derived':True})
    return sorted(out,key=lambda x:-x['similarity'])

"""Caso de demonstração 100% offline (domínios .example / IPs de documentação RFC 5737). Usado em testes, GIF e botão 'Demo'."""
from __future__ import annotations
from pathlib import Path
import tempfile
from ..models import Observation
from ..utils import extract_iocs, refang
from ..evidence.ledger import build as build_ledger
from ..ai.hybrid import extract_hybrid, correlate_entities
from ..intelligence.br_lures import detect_br_lures
from ..intelligence.decision_objects import build_ioc_decisions
from ..intelligence.warninglists import WarningListEngine
from ..timeline import build_timeline, timeline_markdown
from ..correlation.registration import registration_batches
from ..reporting.stix import bundle_from_iocs
from ..reporting.misp import misp_event
from ..intelligence.sigma import sigma_rules
from ..intelligence.legit_domains import partition_iocs

DEMO_LURE=("Receita Federal: seu CPF está irregular. Regularize hoje em hxxps://receita-regulariza[.]example/cpf "
           "ou fale com o atendimento https://wa.me/5511999990000. Não perca o prazo. Banco Aurora S.A.")

DEMO_OWNERSHIP={
 'receita-regulariza.example':{'dns':{'A':['203.0.113.17'],'NS':['ns1.hostbarato.example']},
    'rdap':{'registrar_orgs':['Registrar Exemplo Ltda'],'registrant_orgs':[],'created':'2026-09-20T10:00:05Z','nameservers':['ns1.hostbarato.example']},
    'cert_names':['receita-regulariza.example','pagamento.receita-regulariza.example','www.receita-regulariza.example']},
 'regulariza-cpf.example':{'dns':{'A':['203.0.113.17'],'NS':['ns1.hostbarato.example']},
    'rdap':{'registrar_orgs':['Registrar Exemplo Ltda'],'registrant_orgs':[],'created':'2026-09-20T10:00:41Z','nameservers':['ns1.hostbarato.example']},'cert_names':['regulariza-cpf.example']},
}

def demo_result() -> dict:
    from .app import relationship_rows   # import tardio: evita ciclo
    text=refang(DEMO_LURE); iocs=extract_iocs(text)
    obs=[Observation(d,'domain','manual/input',d,observed_at='2026-09-25T07:00:00+00:00') for d in iocs.get('domain',[])]
    for dom,data in DEMO_OWNERSHIP.items():
        for rtype,vals in data['dns'].items():
            obs+=[Observation(dom,'domain',f'dns:{rtype}',v,observed_at=f'2026-09-2{i}T10:00:00+00:00') for i,v in enumerate(vals)]
        obs+=[Observation(dom,'domain','rdap:registrar_org',o,observed_at='2026-09-25T08:30:00+00:00') for o in data['rdap']['registrar_orgs']]
        obs+=[Observation(dom,'domain','crt.sh',n,observed_at='2026-09-25T08:00:00+00:00') for n in data['cert_names']]
    ledger=build_ledger(obs,{'dns':.7,'rdap':.8,'crt.sh':.85,'manual':.5})
    rels=relationship_rows(DEMO_OWNERSHIP)
    ents=extract_hybrid(DEMO_LURE)
    known=set(ledger['entity'])|set(ledger['value'])
    edges=correlate_entities(ents,known)
    spec=[('domain','receita-regulariza.example',.85,9,4,True),('domain','regulariza-cpf.example',.6,5,3,True),
          ('ip','203.0.113.17',.45,3,2,False),('url','https://receita-regulariza.example/cpf',.72,7,3,True)]
    cands=[{'value':v,'type':t,'confidence':c,'active':act,'evidence_count':ev,'source_families':fam,'campaign':'DEMO-001','context':{},'rationale':['Demonstração']}
           for t,v,c,ev,fam,act in spec]
    decisions=build_ioc_decisions(cands,WarningListEngine())
    out=Path(tempfile.mkdtemp(prefix='tropeiro_demo_'))
    all_iocs,ctx=partition_iocs({'domain':list(DEMO_OWNERSHIP),'ip':['203.0.113.17'],'url':iocs.get('url',[])})
    (out/'stix.json').write_text(bundle_from_iocs(all_iocs,case_id='DEMO-001',context_only=ctx).serialize(pretty=True),encoding='utf-8')
    import json; (out/'misp.json').write_text(json.dumps(misp_event('DEMO-001',all_iocs,context_only=ctx),indent=2),encoding='utf-8')
    for k,v in sigma_rules(all_iocs,'DEMO-001').items(): (out/f'sigma_{k}.yml').write_text(v+'\n',encoding='utf-8')
    summary={'case_id':'DEMO-001','target':'Isca "Receita Federal" (demonstração offline)','evidence':len(ledger),'relationships':len(rels),
             'sources_ok':3,'sources_failed':0,'memory_matches':1,'ai':'Extração híbrida: regras + (GLiNER opcional)'}
    return {'summary':summary,'iocs':decisions,'relationships':rels,'evidence':ledger.to_dict('records'),'sources':[
              {'source':'dns','status':'OK'},{'source':'rdap','status':'OK'},{'source':'crt.sh','status':'OK'}],
            'hybrid_entities':ents,'ai_edges':edges,'lures':detect_br_lures(DEMO_LURE),
            'timeline_md':timeline_markdown(build_timeline(ledger)),
            'related_cases':[{'case_id':'CASE-2026-07','similarity':.82,'shared':'IP 203.0.113.17, NS ns1.hostbarato.example'}],
            'batches':registration_batches([{'domain':d,'created':v['rdap']['created'],'registrar':'; '.join(v['rdap']['registrar_orgs']),'nameservers':v['rdap']['nameservers']} for d,v in DEMO_OWNERSHIP.items()]),
            'similar_lures':[{'case_id':'CASE-2026-07','similarity':0.88,'derived':True}],
            'exports':[str(p) for p in sorted(out.iterdir())],'report_path':None,'package_path':None}

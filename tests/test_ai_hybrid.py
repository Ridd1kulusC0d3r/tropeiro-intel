from tropeiro.ai import extract_hybrid, correlate_entities, lure_similarity, run_qwen_analysis, enforce_evidence_support
from tropeiro.utils import refang

TEXT=('Receita Federal: regularize seu CPF 529.982.247-25 em hxxps://receita-gov[.]example/cpf '
      'ou WhatsApp https://wa.me/5511999990000. Atenciosamente, Banco Aurora.')

class FakeGliner:
    def predict_entities(self,text,labels,threshold=.45):
        return [{'text':'receita-gov.example','label':'domain','score':.7,'start':0,'end':1},
                {'text':'Banco Aurora','label':'organization','score':.8,'start':0,'end':1},
                {'text':'nao e dominio!!','label':'domain','score':.9,'start':0,'end':1},
                {'text':'999.999.1.1','label':'ip address','score':.9,'start':0,'end':1}]

def test_refang():
    assert refang('hxxps://a[.]b[@]c(dot)com')=='https://a.b@c.com'

def test_rules_only_works_without_model():
    ents={(e['type'],e['value']):e for e in extract_hybrid(TEXT)}
    assert ('domain','receita-gov.example') in ents and ('cpf','52998224725') in ents
    assert ('whatsapp','5511999990000') in ents and ('brand','Receita Federal') in ents
    assert all(e['derived'] and not e['analyst_confirmed'] for e in ents.values())

def test_agreement_boosts_and_invalid_model_output_is_dropped():
    ents={(e['type'],e['value']):e for e in extract_hybrid(TEXT,gliner=FakeGliner())}
    d=ents[('domain','receita-gov.example')]
    assert d['methods']==['rule','gliner'] and d['score']>.9
    assert ('org','Banco Aurora') in ents and ents[('org','Banco Aurora')]['methods']==['gliner']
    assert not any(v=='nao e dominio!!' or v=='999.999.1.1' for _,v in ents)

def test_correlate_links_to_known_entities():
    ents=extract_hybrid(TEXT,gliner=FakeGliner())
    edges=correlate_entities(ents,['receita-gov.example','login.receita-gov.example','Banco Aurora SA'])
    rel={(e['src'],e['dst'],e['relation']) for e in edges}
    assert ('receita-gov.example','receita-gov.example','same_value') in rel
    assert ('Banco Aurora','Banco Aurora SA','similar_name') in rel
    assert ('receita-gov.example','login.receita-gov.example','same_root_domain') in rel

def test_lure_similarity():
    r=lure_similarity('Sua conta precisa de validação, acesse o link para regularizar',
                      {'A':'Sua conta precisa de validação! Acesse o link para regularizar','B':'promoção de verão'})
    assert [x['case_id'] for x in r]==['A']

class FakeChat:
    def __init__(self,outs): self.outs=list(outs)
    def chat(self,system,user,max_new_tokens=0): return self.outs.pop(0)

PACKET={'schema':'x','evidence_ledger':[{'evidence_id':'EV-1'}],'packet_sha256':'h'}

def test_qwen_retry_and_downgrade():
    good='{"executive_summary":"s","key_findings":[{"statement":"a","analytic_type":"observed","confidence":"HIGH","evidence_refs":["EV-404"]},{"statement":"b","analytic_type":"observed","confidence":"HIGH","evidence_refs":["EV-1"]}]}'
    out=run_qwen_analysis(FakeChat(['isto não é json',good]),PACKET)
    assert out['_generation_status']=='OK_RETRY'
    f=out['key_findings']
    assert f[0]['analytic_type']=='hypothesis' and f[0]['confidence']=='INSUFFICIENT' and f[0]['evidence_refs']==[]
    assert f[1]['analytic_type']=='observed' and out['_validation']['downgraded_findings']==1

def test_valid_ref_but_unrelated_claim_is_downgraded():
    """Caso real (Qwen3-0.6B): citou um ev_id existente para uma afirmação sem relação com ele."""
    from tropeiro.ai import enforce_evidence_support
    packet={'evidence_ledger':[{'evidence_id':'ev-1','entity':'receita-regulariza.example','entity_type':'domain','source':'manual/input','value':'receita-regulariza.example'}]}
    a={'key_findings':[
        {'statement':'seu CPF está irregular.','analytic_type':'observed','confidence':'HIGH','evidence_refs':['ev-1'],'basis':'Observado na página de entrada do site.'},
        {'statement':'O domínio receita-regulariza.example foi informado como alvo.','analytic_type':'observed','confidence':'HIGH','evidence_refs':['ev-1'],'basis':'entrada manual'}],
       'hypotheses':[{'hypothesis':'h','support_refs':['ev-1'],'contradiction_refs':['ev-1']}]}
    out=enforce_evidence_support(a,packet)
    bad,good=out['key_findings']
    assert bad['analytic_type']=='hypothesis' and bad['confidence']=='LOW' and bad['_flag']=='evidence_mismatch'
    assert good['analytic_type']=='observed' and good['confidence']=='HIGH' and '_flag' not in good
    assert out['hypotheses'][0]['contradiction_refs']==[] and out['hypotheses'][0]['_flags'][0]=='refs_overlap' and 'evidence_mismatch' in out['hypotheses'][0]['_flags']
    assert out['_validation']['mismatched_findings']==2 and out['_validation']['downgraded_findings']==1

def test_hypothesis_without_support_and_unreferenced_detection_are_flagged():
    from tropeiro.ai import enforce_evidence_support, analysis_request
    a={'hypotheses':[{'hypothesis':'h','support_refs':[],'contradiction_refs':[],'confidence':'HIGH'}],
       'detection_opportunities':[{'surface':'dns','idea':'x','evidence_refs':[]}]}
    out=enforce_evidence_support(a,{})
    assert out['hypotheses'][0]['confidence']=='INSUFFICIENT' and out['hypotheses'][0]['_flag']=='no_support'
    assert out['detection_opportunities'][0]['_flag']=='no_evidence' and out['_validation']['downgraded_findings']==1
    req=analysis_request({'evidence_ledger':[{'evidence_id':'ev-abc'}],'packet_sha256':'h'})
    assert 'IDS_DE_EVIDENCIA_VALIDOS' in req and '"ev-abc"' in req          # o modelo recebe a lista de ids reais

def test_qwen_chat_is_deterministic_by_default():
    from tropeiro.ai import QwenLocalChat
    assert QwenLocalChat('x').deterministic is True and QwenLocalChat('x',deterministic=False).deterministic is False


def test_hypothesis_with_unrelated_support_is_capped():
    from tropeiro.ai import enforce_evidence_support
    packet={'evidence_ledger':[{'evidence_id':'ev-1','entity':'receita-regulariza.example','source':'dns:A','value':'203.0.113.17'}]}
    out=enforce_evidence_support({'hypotheses':[
        {'hypothesis':'O CPF do usuário está irregular','support_refs':['ev-1'],'contradiction_refs':[],'confidence':'HIGH'},
        {'hypothesis':'receita-regulariza.example resolve para 203.0.113.17','support_refs':['ev-1'],'contradiction_refs':[],'confidence':'HIGH'}]},packet)
    bad,good=out['hypotheses']
    assert bad['confidence']=='LOW' and bad['_flag']=='evidence_mismatch'
    assert good['confidence']=='HIGH' and '_flag' not in good

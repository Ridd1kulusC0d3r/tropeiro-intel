import re
PT_TERMS={"conta","pix","boleto","cpf","brasil","regularize","bloqueio","fatura","banco","senha"};EN_TERMS={"account","invoice","password","verify","payment","bank","login","urgent"};SECTORS={"banking":{"pix","banco","bank","boleto","conta","account","cartao","card"},"government":{"gov","receita","cpf","imposto","tax","beneficio"},"retail":{"pedido","delivery","entrega","loja","order","shipping"},"technology":{"microsoft","google","office","cloud","password","login"}};OBJECTIVE_WORDS={"credentials":{"login","senha","password","credential","verify","conta","account"},"financial_fraud":{"pix","boleto","payment","pagamento","transfer","cartao","card"}}

def infer_victimology(lure_text="",brand="",urls=None,titles=None):
    text=" ".join([lure_text or "",brand or ""]+list(urls or [])+list(titles or [])).lower();tokens=set(re.findall(r"[\wáéíóúãõç]+",text));pt=len(tokens&PT_TERMS);en=len(tokens&EN_TERMS);language="pt-BR" if pt>en and pt else ("en" if en>pt and en else "unknown");sectors=[]
    for sec,terms in SECTORS.items():
        score=len(tokens&terms)
        if score:sectors.append((sec,score))
    sectors.sort(key=lambda x:x[1],reverse=True);objectives=[]
    for obj,terms in OBJECTIVE_WORDS.items():
        score=len(tokens&terms)
        if score:objectives.append((obj,score))
    return {"language":language,"impersonated_brand":brand or None,"likely_sectors":[x[0] for x in sectors[:3]],"likely_victim_region":"Brazil" if language=="pt-BR" else None,"lure_objective_signals":[x[0] for x in sorted(objectives,key=lambda x:x[1],reverse=True)],"confidence":"MODERATE" if (pt+en)>=2 or sectors else "LOW"}

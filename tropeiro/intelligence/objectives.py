import re
RULES={"credential_theft":{"login","signin","senha","password","credential","verify","verifique","conta"},"financial_fraud":{"pix","boleto","payment","pagamento","transfer","transferencia","cartao","card"},"malware_delivery":{"download","baixar","apk","exe","msi","zip","attachment","anexo"},"account_takeover":{"mfa","otp","2fa","session","sessao","cookie","código","codigo"},"brand_abuse":{"suporte","support","official","oficial","segurança","security"}}

def infer_objectives(text="", urls=None):
    corpus=(" ".join([text or ""]+list(urls or []))).lower();tokens=set(re.findall(r"[\wáéíóúãõç]+",corpus));scores={k:len(tokens&v) for k,v in RULES.items()};ranked=[{"objective":k,"signal_count":v} for k,v in sorted(scores.items(),key=lambda x:x[1],reverse=True) if v]
    return {"ranked":ranked,"primary":ranked[0]["objective"] if ranked else "unknown","confidence":"MODERATE" if ranked and ranked[0]["signal_count"]>=2 else "LOW"}

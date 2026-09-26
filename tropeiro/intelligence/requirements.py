from dataclasses import dataclass, asdict
from typing import List

@dataclass
class IntelligenceRequirement:
    id:str;question:str;priority:str="P2";decision_supported:str="";collection_needed:List[str]=None;status:str="OPEN"
    def to_dict(self):
        d=asdict(self);d["collection_needed"]=d["collection_needed"] or [];return d

def default_phishing_requirements():
    return [
        IntelligenceRequirement("PIR-01","A campanha continua operacional?","P1","bloqueio, hunting e takedown",["DNS","urlscan","HTTP/status indireto","threat intel"]),
        IntelligenceRequirement("PIR-02","Existem novos domínios/URLs associados ao mesmo operador?","P1","expansão de bloqueio e hunting",["CT","dnstwist","FOFA","Censys","DNSDumpster","urlscan"]),
        IntelligenceRequirement("PIR-03","Quais IOCs podem ser bloqueados com baixo risco de falso positivo?","P1","bloqueio preventivo",["warninglists","source diversity","last_seen","shared hosting checks"]),
        IntelligenceRequirement("PIR-04","Há evidência suficiente para takedown?","P1","abuse/takedown",["RDAP","registrar","hosting","screenshots/third-party scan","timestamps"]),
        IntelligenceRequirement("PIR-05","Qual é o provável objetivo da campanha e quem é visado?","P2","prioridade de defesa e comunicação",["lure text","language","brand","paths","forms"]),
        IntelligenceRequirement("PIR-06","Há evidência de controle operacional comum ou atribuição a entidade conhecida?","P2","campaign attribution",["registration","TLS","trackers","JARM","redirects","contacts"]),
        IntelligenceRequirement("PIR-07","Qual é o próximo pivô de maior valor investigativo?","P2","reduzir tempo do analista",["graph degree","novelty","discrimination","source reliability"]),
        IntelligenceRequirement("PIR-08","Quais lacunas impedem uma conclusão mais forte?","P2","collection planning",["coverage matrix","missing evidence","confidence dimensions"])]

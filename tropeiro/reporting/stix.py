import uuid
from datetime import datetime, timedelta, timezone
from stix2 import (Bundle, Campaign, DomainName, EmailAddress, IPv4Address, Indicator, Relationship,
                   URL, parse, TLP_WHITE, TLP_GREEN, TLP_AMBER, TLP_RED)

TLP={'WHITE':TLP_WHITE,'CLEAR':TLP_WHITE,'GREEN':TLP_GREEN,'AMBER':TLP_AMBER,'RED':TLP_RED}
PATTERN={'domain':'domain-name:value','url':'url:value','ip':'ipv4-addr:value','email':'email-addr:value'}
SCO={'domain':DomainName,'url':URL,'ip':IPv4Address,'email':EmailAddress}
NS=uuid.UUID('7b1d2f4a-0c5e-4a9b-9d3e-5a6f1c2b8e01')

def _esc(v): return str(v).replace('\\','\\\\').replace("'","\\'")

def bundle_from_iocs(iocs,case_id=None,tlp='AMBER',confidence=None,valid_days=90,campaign_name=None,context_only=None):
    """Observáveis (como antes) + Indicators com validade, Campaign e Relationships.

    `context_only`: IOCs de plataformas legítimas; entram só como observáveis, sem Indicator.
    `confidence` é 0-100 (escala STIX); se None, os Indicators não declaram confiança.
    IDs são determinísticos (uuid5) para o mesmo caso+valor: reexportar não duplica no TIP.
    """
    marking=TLP.get(str(tlp).upper(),TLP_AMBER)
    now=datetime.now(timezone.utc).replace(microsecond=0)
    objs=[marking]
    camp=None
    if case_id:
        camp=Campaign(id=f'campaign--{uuid.uuid5(NS,f"campaign:{case_id}")}',name=campaign_name or f'Tropeiro case {case_id}',
                      first_seen=now,object_marking_refs=[marking.id])
        objs.append(camp)
    for typ,sco in SCO.items():
        for v in iocs.get(typ,[]):
            s=sco(value=v)
            objs.append(s)
            kw={}
            if confidence is not None: kw['confidence']=int(confidence)
            ind=Indicator(id=f'indicator--{uuid.uuid5(NS,f"{case_id}:{typ}:{v}")}',
                          name=f'{typ}: {v}',pattern=f"[{PATTERN[typ]} = '{_esc(v)}']",pattern_type='stix',
                          valid_from=now,valid_until=now+timedelta(days=valid_days),
                          indicator_types=['malicious-activity'],labels=['phishing'],
                          object_marking_refs=[marking.id],**kw)
            objs.append(ind)
            objs.append(Relationship(ind,'based-on',s))
            if camp: objs.append(Relationship(ind,'indicates',camp))
    for typ,sco in SCO.items():
        for v in (context_only or {}).get(typ,[]): objs.append(sco(value=v))
    return Bundle(*objs,allow_custom=True)

def validate(serialized): return parse(serialized,allow_custom=True)

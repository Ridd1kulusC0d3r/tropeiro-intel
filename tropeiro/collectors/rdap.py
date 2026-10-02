from ..http import get
from ..utils import valid_hostname

def _vcard(entity):
    data={}
    vc=entity.get("vcardArray")
    if not isinstance(vc,list) or len(vc)<2: return data
    for row in vc[1]:
        if not isinstance(row,list) or len(row)<4: continue
        key=str(row[0]).lower(); value=row[3]
        if key in ("fn","org","email","tel"):
            if isinstance(value,list): value=" ".join(map(str,value))
            data.setdefault(key,[]).append(str(value))
    return data

def lookup(domain):
    dom=valid_hostname(domain)
    if not dom: raise ValueError(f'hostname inválido: {domain!r}')
    d=get(f'https://rdap.org/domain/{dom}')
    events={e.get('eventAction'):e.get('eventDate') for e in d.get('events',[])}
    entities=[]
    for e in d.get("entities",[]) or []:
        entities.append({"handle":e.get("handle"),"roles":e.get("roles",[]),"public_vcard":_vcard(e)})
    registrar_orgs=[]; registrant_orgs=[]
    for e in entities:
        orgs=e["public_vcard"].get("org",[])
        if "registrar" in e["roles"]: registrar_orgs += orgs
        if "registrant" in e["roles"]: registrant_orgs += orgs
    return {'handle':d.get('handle'),'status':d.get('status',[]),'created':events.get('registration'),'updated':events.get('last changed'),'expires':events.get('expiration'),'nameservers':[x.get('ldhName','').lower() for x in d.get('nameservers',[])],'entities':entities,'registrar_orgs':sorted(set(registrar_orgs)),'registrant_orgs':sorted(set(registrant_orgs)),'port43':d.get("port43"),'secure_dns':d.get("secureDNS",{})}

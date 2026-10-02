# Só estes tipos vão para IDS por padrão; e-mail/telefone são contexto, não bloqueio.
IDS_BY_DEFAULT={'domain','url','ip','hash'}
TLP_TAG={'WHITE':'tlp:white','CLEAR':'tlp:clear','GREEN':'tlp:green','AMBER':'tlp:amber','RED':'tlp:red'}

def _hash_type(v): return {32:'md5',40:'sha1',64:'sha256'}.get(len(v),'sha256')

def misp_event(case_id,iocs,info='Tropeiro Intel phishing investigation',tlp='AMBER',to_ids=None):
    """`to_ids`: conjunto de tipos que viram `to_ids=True`; padrão = IDS_BY_DEFAULT."""
    ids=IDS_BY_DEFAULT if to_ids is None else set(to_ids)
    mapping={'domain':'domain','url':'url','ip':'ip-dst','email':'email-dst','phone':'phone-number'}
    cats={'email':'Payload delivery','phone':'Other'}
    attrs=[]
    for typ,vals in iocs.items():
        for v in vals:
            if typ=='hash': mtype=_hash_type(v)
            elif typ in mapping: mtype=mapping[typ]
            else: continue
            attrs.append({'type':mtype,'category':cats.get(typ,'Network activity' if typ!='hash' else 'Payload delivery'),
                          'to_ids':typ in ids,'value':v,'comment':'Exported by Tropeiro Intel'})
    tags=[{'name':TLP_TAG.get(str(tlp).upper(),'tlp:amber')},{'name':'type:phishing'}]
    return {'Event':{'info':f'{info} - {case_id}','distribution':0,'threat_level_id':2,'analysis':1,'Tag':tags,'Attribute':attrs}}

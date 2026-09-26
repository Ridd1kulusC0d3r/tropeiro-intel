def misp_event(case_id,iocs,info='Tropeiro Intel phishing investigation'):
    attrs=[];mapping={'domain':'domain','url':'url','ip':'ip-dst','email':'email-dst','hash':'sha256'}
    for typ,vals in iocs.items():
        for v in vals:
            if typ in mapping:attrs.append({'type':mapping[typ],'category':'Network activity','to_ids':True,'value':v,'comment':'Exported by Tropeiro Intel'})
    return {'Event':{'info':f'{info} - {case_id}','distribution':0,'threat_level_id':2,'analysis':1,'Attribute':attrs}}

from stix2 import Bundle, DomainName, URL, IPv4Address, EmailAddress, parse

def bundle_from_iocs(iocs):
    objs=[]
    for d in iocs.get('domain',[]): objs.append(DomainName(value=d))
    for u in iocs.get('url',[]): objs.append(URL(value=u))
    for ip in iocs.get('ip',[]): objs.append(IPv4Address(value=ip))
    for e in iocs.get('email',[]): objs.append(EmailAddress(value=e))
    return Bundle(*objs, allow_custom=True)

def validate(serialized): return parse(serialized,allow_custom=True)

from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class ProviderSpec:
    name:str;capabilities:tuple;secret_names:tuple=();cost_class:str='free';default_enabled:bool=False;passive:bool=True;max_calls:int=20

REGISTRY={x.name:x for x in [
 ProviderSpec('dns',('dns','infrastructure'),(), 'free',True,True,100),
 ProviderSpec('rdap',('registration','ownership'),(), 'free',True,True,50),
 ProviderSpec('crt.sh',('tls','subdomains'),(), 'free',True,True,30),
 ProviderSpec('wayback',('historical_web',),(), 'free',True,True,20),
 ProviderSpec('commoncrawl',('historical_web',),(), 'free',False,True,20),
 ProviderSpec('urlscan',('web_scan','redirects','web_fingerprint'),('URLSCAN_API_KEY',),'free_optional',True,True,30),
 ProviderSpec('otx',('threat_intel',),(), 'free',True,True,20),
 ProviderSpec('virustotal',('threat_intel','relationships'),('VT_API_KEY',),'quota',False,True,20),
 ProviderSpec('threatfox',('threat_intel',),('THREATFOX_AUTH_KEY',),'free_optional',False,True,20),
 ProviderSpec('dnsdumpster',('dns','infrastructure','asn'),('DNSDUMPSTER_API_KEY',),'quota',False,True,20),
 ProviderSpec('fofa',('internet_scan','jarm','tls'),('FOFA_API_KEY',),'paid_optional',False,True,10),
 ProviderSpec('censys',('internet_scan','tls','asn'),('CENSYS_PAT',),'paid_optional',False,True,10),
 ProviderSpec('domaintools',('historical_whois','reverse_whois'),('DOMAINTOOLS_API_KEY',),'enterprise',False,True,10),
 ProviderSpec('securitytrails',('passive_dns','historical_whois'),('SECURITYTRAILS_API_KEY',),'paid_optional',False,True,10),
 ProviderSpec('whoisxml',('historical_whois','reverse_whois'),('WHOISXML_API_KEY',),'paid_optional',False,True,10),
]}


def plan(requirements,secrets=None,feature_flags=None,budget='balanced'):
    secrets=secrets or {};feature_flags=feature_flags or {};req=set(requirements or [])
    rows=[]
    for name,s in REGISTRY.items():
        useful=bool(req & set(s.capabilities)) or not req
        enabled=feature_flags.get(name,s.default_enabled)
        missing=[x for x in s.secret_names if not secrets.get(x)]
        if not useful:status='NOT_NEEDED'
        elif not enabled:status='DISABLED'
        elif missing:status='SKIPPED_MISSING_SECRET'
        elif budget=='free' and s.cost_class in {'paid_optional','enterprise'}:status='SKIPPED_BUDGET'
        else:status='READY'
        rows.append({**asdict(s),'status':status,'missing_secrets':missing,'matched_capabilities':sorted(req&set(s.capabilities))})
    return rows

import ipaddress
DEFAULT_PUBLIC_RESOLVERS={"8.8.8.8","8.8.4.4","1.1.1.1","1.0.0.1","9.9.9.9","149.112.112.112"};DEFAULT_SHARED_PROVIDERS={"cloudflare","amazon","aws","google","microsoft","azure","akamai","fastly","digitalocean","ovh","hetzner","oracle","linode","vultr"}
class WarningListEngine:
    def __init__(self,public_resolvers=None,shared_provider_terms=None):self.public_resolvers=set(public_resolvers or DEFAULT_PUBLIC_RESOLVERS);self.shared_provider_terms=set(shared_provider_terms or DEFAULT_SHARED_PROVIDERS)
    def check(self,value,context=None):
        value=str(value or "").strip();context=context or {};hits=[]
        try:
            ipaddress.ip_address(value)
            if value in self.public_resolvers:hits.append({"type":"public_dns_resolver","severity":"high","reason":"Well-known public resolver; unsafe to treat as campaign-specific."})
            if context.get("shared_host_count",0) and context["shared_host_count"]>50:hits.append({"type":"shared_ip","severity":"high","reason":f"IP appears shared by {context['shared_host_count']}+ hosts."})
        except Exception:pass
        provider=" ".join(map(str,[context.get("provider",""),context.get("asn_owner","")])).lower()
        if any(x in provider for x in self.shared_provider_terms):hits.append({"type":"shared_cloud_or_cdn","severity":"medium","reason":"Common cloud/CDN provider; infrastructure ownership is not operator attribution."})
        if context.get("known_legitimate"):hits.append({"type":"known_legitimate","severity":"high","reason":"Value is present in locally trusted/legitimate context."})
        return hits
    def actionability_penalty(self,hits):
        sev={"low":.05,"medium":.20,"high":.45};return min(.8,sum(sev.get(x.get("severity"),0) for x in hits))

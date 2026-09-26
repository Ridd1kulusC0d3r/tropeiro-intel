import networkx as nx, ipaddress, re

NODE_PREFIX_TYPES={"cert:":"certificate","asn:":"asn","org:":"organization","registrar:":"registrar","tracker:":"tracker","provider:":"provider","netblock:":"netblock"}

def node_type(v):
    s=str(v)
    for p,t in NODE_PREFIX_TYPES.items():
        if s.startswith(p): return t
    if s.startswith(('http://','https://')): return 'url'
    try: ipaddress.ip_address(s); return 'ip'
    except Exception: pass
    if '@' in s: return 'email'
    digits=re.sub(r'\D','',s)
    if 10 <= len(digits) <= 15 and digits == re.sub(r'\D','',s): return 'phone'
    if '.' in s: return 'domain'
    return 'artifact'

class CampaignGraph:
    def __init__(self): self.g=nx.Graph()
    def add_node(self,value,node_type_override=None,**attrs):
        if not value:return
        nt=node_type_override or node_type(value); current=self.g.nodes.get(value,{})
        self.g.add_node(value,**{**current,**attrs,"node_type":nt})
    def add_rel(self,a,b,relation,source,weight=1.0,**attrs):
        if not a or not b or a==b:return
        self.add_node(a);self.add_node(b)
        if self.g.has_edge(a,b):
            e=self.g[a][b];e['relations']=sorted(set(e.get('relations',[])+[relation]));e['sources']=sorted(set(e.get('sources',[])+[source]));e['weight']=max(e.get('weight',0),weight);e['evidence_count']=int(e.get('evidence_count',1))+1
        else:self.g.add_edge(a,b,relations=[relation],sources=[source],weight=weight,evidence_count=1,**attrs)
    def clusters(self):return sorted(nx.connected_components(self.g),key=len,reverse=True)
    def ownership_edges(self):return [(a,b,d) for a,b,d in self.g.edges(data=True) if any(r in {"registered_by","registrant_org","asn_owner","hosted_by_provider","operated_by_candidate"} for r in d.get("relations",[]))]

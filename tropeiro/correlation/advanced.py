from collections import defaultdict
from math import prod
import networkx as nx

RELATION_META={
 'same_tracker':('tracking',.98,.98),
 'same_public_contact':('identity',.96,.98),
 'same_registrant_org':('registration',.92,.94),
 'same_certificate':('tls',.86,.88),
 'same_web_fingerprint':('content',.84,.86),
 'same_redirect':('web',.82,.86),
 'same_jarm':('service',.68,.72),
 'same_ns':('dns',.58,.56),
 'same_mx':('dns',.54,.56),
 'same_ip':('infrastructure',.30,.34),
 'same_asn':('infrastructure',.22,.24),
 'same_provider':('infrastructure',.10,.12),
 'same_registrar':('registration',.18,.18),
 'lexical_similarity':('domain_similarity',.50,.62),
}
COMMON_ONLY={'same_ip','same_asn','same_provider','same_registrar'}


def source_family(source):
    s=str(source or '').lower()
    if s.startswith('rdap') or 'whois' in s:return 'registration'
    if s.startswith('dns') or 'dnsdumpster' in s:return 'dns'
    if 'censys' in s or 'fofa' in s or 'shodan' in s or 'netlas' in s:return 'internet_scan'
    if 'urlscan' in s:return 'web_scan'
    if 'crt' in s or 'certificate' in s:return 'tls'
    if any(x in s for x in ('threatfox','virustotal','otx','urlhaus','phishtank','openphish')):return 'threat_intel'
    if 'manual' in s:return 'analyst_input'
    return s.split(':')[0] or 'unknown'


def source_independence(observations):
    fam=defaultdict(lambda:{'sources':set(),'count':0})
    for o in observations:
        src=o.get('source') if isinstance(o,dict) else getattr(o,'source','')
        f=source_family(src); fam[f]['sources'].add(str(src));fam[f]['count']+=1
    return [{'family':k,'sources':sorted(v['sources']),'observations':v['count'],'independent_unit':1} for k,v in sorted(fam.items())]


def relationship_strength(evidence,prevalence=0.0):
    vals=[];families=set();discriminating=0
    for e in evidence or []:
        code=e.get('code') or e.get('relation')
        cat,base,disc=RELATION_META.get(code,('other',.35,.35))
        rel=float(e.get('source_reliability',.75)); prev=float(e.get('prevalence',prevalence) or 0)
        common_penalty=max(.15,1-min(.85,prev))
        v=min(.98,base*disc*rel*common_penalty)
        vals.append(v);families.add(e.get('source_family') or source_family(e.get('source')))
        if disc>=.70:discriminating+=1
    score=1-prod(1-v for v in vals) if vals else 0.0
    if len(families)<2:score=min(score,.59)
    if discriminating==0:score=min(score,.64)
    return {'score':round(score,4),'independent_source_families':len(families),'discriminating_signals':discriminating}


def guarded_components(graph,min_weight=.45):
    """Build clusters without letting common infrastructure become a universal bridge."""
    h=nx.Graph()
    for n,d in graph.nodes(data=True):h.add_node(n,**d)
    for a,b,d in graph.edges(data=True):
        rels=set(d.get('relations',[])); w=float(d.get('weight',0) or 0)
        if w<min_weight:continue
        if rels and rels.issubset(COMMON_ONLY):continue
        h.add_edge(a,b,**d)
    return sorted(nx.connected_components(h),key=len,reverse=True),h

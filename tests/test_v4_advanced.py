import json, ast
import networkx as nx
from pathlib import Path
from tropeiro.similarity import domain_similarity,compare_domains,extract_durable_identifiers
from tropeiro.correlation.advanced import source_independence,guarded_components,relationship_strength
from tropeiro.intelligence.negative_evidence import evaluate_negative_evidence
from tropeiro.intelligence.takeover import assess_passive_exposure
from tropeiro.providers import plan


def test_domain_similarity_high_for_tld_swap():
    r=domain_similarity('secure-brand.com','secure-brand.net')
    assert r['score']>.7
    assert 'tld_swap' in r['reasons']

def test_candidate_similarity_is_not_verdict():
    rows=compare_domains(['example.com','example.net','totallydifferent.org'],min_score=.4)
    assert all('score' in x and 'reasons' in x for x in rows)

def test_durable_identifiers_from_passive_result():
    x=extract_durable_identifiers({'data':{'redirects':['https://r.example/x']},'payload':'GTM-ABC123 and G-ABCDEF12'})
    assert any(i['type']=='google_tag_manager' for i in x['identifiers'])
    assert 'https://r.example/x' in x['redirects']

def test_source_independence_groups_families():
    rows=source_independence([{'source':'rdap:x'},{'source':'rdap:y'},{'source':'urlscan'}])
    fam={x['family']:x for x in rows}
    assert fam['registration']['observations']==2
    assert fam['web_scan']['observations']==1

def test_cluster_guard_drops_common_only_bridge():
    g=nx.Graph();g.add_edge('a','b',relations=['same_asn'],weight=.8);g.add_edge('b','c',relations=['same_tracker'],weight=.9)
    comps,h=guarded_components(g,.4)
    assert not h.has_edge('a','b')
    assert h.has_edge('b','c')

def test_relationship_strength_caps_single_family():
    r=relationship_strength([{'code':'same_tracker','source_family':'web_scan','source_reliability':1.0}])
    assert r['score']<=.59

def test_negative_evidence_never_claims_identity():
    rows=evaluate_negative_evidence({'rdap_checked':True,'registrant_org_present':False})
    assert rows and all('absence_type' in x for x in rows)

def test_takeover_passive_only():
    r=assess_passive_exposure('a.example',['x.github.io'],resolver=lambda *a:[])[0]
    assert r['status']=='POTENTIALLY_DANGLING'
    assert r['validation']=='AUTHORIZED_VALIDATION_REQUIRED'

def test_provider_planner_missing_key_is_skip():
    rows=plan(['internet_scan'],{}, {'censys':True}, 'balanced')
    c=[x for x in rows if x['name']=='censys'][0]
    assert c['status']=='SKIPPED_MISSING_SECRET'

def test_official_notebook_compiles():
    p=Path(__file__).parents[1]/'notebooks'/'Tropeiro_Intel_Official_Colab.ipynb'
    nb=json.loads(p.read_text())
    assert len(nb['cells'])>=60
    for cell in nb['cells']:
        if cell.get('cell_type')=='code':
            src=cell.get('source','')
            if isinstance(src,list):src=''.join(src)
            ast.parse(src)

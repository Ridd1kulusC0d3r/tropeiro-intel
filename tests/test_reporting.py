from tropeiro.reporting.rich_html import build_report
from tropeiro.reporting.exporter import export_selected,zip_exports
def sample():
    return {'meta':{'case_id':'T-1','analyst':'Analista'},'executive_brief':{'executive_assessment':{'judgment':'Teste','implication':'Agir.'}},'action_matrix':[{'priority':'P1','action':'HUNT','target':'x.test','owner':'SOC','why':'teste'}],'ioc_decisions':[{'ioc':'x.test','ioc_type':'domain','confidence':.9,'actionability':.9,'active_now':True,'false_positive_risk':'LOW','block_recommended':True,'hunt_recommended':True,'takedown_candidate':True}],'confidence':{'malicious_intent':{'score':.9,'band':'HIGH'}},'lifecycle':{'stage':'ACTIVE'},'victimology':{},'objectives':{'primary':'credential_theft'},'collection_gaps':[],'next_best_pivots':[],'attribution_assessments':[],'campaign_clusters':[],'evidence_ledger':[],'source_status':[],'ownership':{},'detection_package':{}}
def test_rich_report_offline(tmp_path):
    p=build_report(sample(),tmp_path/'report.html');t=p.read_text();assert 'Tropeiro Intel' in t;assert '🐂' not in t;assert 'Export Center' in t;assert 'https://' not in t
def test_selective_export(tmp_path):
    data=sample();report=build_report(data,tmp_path/'r.html');files=export_selected(data,tmp_path/'exports',{'report_html','ioc_decisions_csv'},report);names={x.name for x in files};assert 'report.html' in names and 'ioc_decisions.csv' in names and 'action_matrix.csv' not in names;assert zip_exports(files,tmp_path/'x.zip').exists()

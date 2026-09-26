import csv,json,hashlib,zipfile
from pathlib import Path
SUPPORTED={'report_html':'report.html','executive_brief_json':'executive_brief.json','ioc_decisions_csv':'ioc_decisions.csv','action_matrix_csv':'action_matrix.csv','collection_gaps_csv':'collection_gaps.csv','next_best_pivots_csv':'next_best_pivots.csv','evidence_ledger_csv':'evidence_ledger.csv','attribution_csv':'attribution_assessments.csv','detection_json':'detection_package.json','stix_json':'stix_bundle.json','misp_json':'misp_event.json','case_json':'case.json'}
def _write_csv(path,rows):
    rows=rows or []
    if not rows:Path(path).write_text('',encoding='utf-8');return
    cols=list(dict.fromkeys(k for r in rows if isinstance(r,dict) for k in r.keys()))
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader()
        for r in rows:w.writerow({k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v) for k,v in r.items()})
def export_selected(case_data,output_dir,selections,report_path=None):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);created=[];mapping={'executive_brief_json':('json','executive_brief'),'detection_json':('json','detection_package'),'stix_json':('json','stix_bundle'),'misp_json':('json','misp_event'),'case_json':('json',None),'ioc_decisions_csv':('csv','ioc_decisions'),'action_matrix_csv':('csv','action_matrix'),'collection_gaps_csv':('csv','collection_gaps'),'next_best_pivots_csv':('csv','next_best_pivots'),'evidence_ledger_csv':('csv','evidence_ledger'),'attribution_csv':('csv','attribution_assessments')}
    if 'report_html' in selections and report_path:p=out/'report.html';p.write_bytes(Path(report_path).read_bytes());created.append(p)
    for key in selections:
        if key not in mapping:continue
        fmt,data_key=mapping[key];p=out/SUPPORTED[key];obj=case_data if data_key is None else case_data.get(data_key,[] if fmt=='csv' else {})
        if fmt=='json':p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        else:_write_csv(p,obj)
        created.append(p)
    manifest=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in created];mp=out/'manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');created.append(mp);return created
def zip_exports(files,zip_path):
    zp=Path(zip_path)
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:p=Path(p);z.write(p,arcname=p.name)
    return zp

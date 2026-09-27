from pathlib import Path

from tropeiro.reporting.context import safe_dataframe, build_feature_matrix, build_report_data, report_preflight
from tropeiro.reporting.rich_html import build_report
from tropeiro.reporting.exporter import export_selected, zip_exports


def test_safe_dataframe_scalar_dict():
    df=safe_dataframe({"status":"ok","count":1})
    assert list(df.columns)==["status","count"]
    assert len(df)==1


def test_sparse_report_context_does_not_crash(tmp_path):
    ns={"CASE_ID":"TI-SPARSE","ANALYST":"Analyst","MODE":"PASSIVE","WORKSPACE":tmp_path,"ENABLE_DNS":True,"ENABLE_RDAP":True,"ENABLE_CT":True,"ENABLE_DOMAIN_SIMILARITY":True,"ENABLE_PASSIVE_TAKEOVER":True,"STATUS":[{"source":"dns","status":"OK"}]}
    fm=build_feature_matrix(ns)
    assert any(x["status"]=="NOT_RUN" for x in fm)
    data=build_report_data(ns,version="test")
    assert data["meta"]["partial_report"] is True
    p=build_report(data,tmp_path/"report.html")
    assert p.exists()
    files=export_selected(data,tmp_path/"export",{"report_html","case_json"},p)
    assert any(x.name=="case.json" for x in files)
    assert zip_exports(files,tmp_path/"bundle.zip").exists()


def test_preflight_only_requires_case_and_workspace(tmp_path):
    r=report_preflight({"CASE_ID":"X","WORKSPACE":tmp_path})
    assert r["ready"] is True
    assert r["optional_missing"]

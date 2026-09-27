from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
import pandas as pd


def _ns_get(ns: Mapping[str, Any], name: str, default: Any):
    value = ns.get(name, default)
    return default if value is None else value


def safe_len(value: Any) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except Exception:
        return 1


def safe_dataframe(value: Any) -> pd.DataFrame:
    """Turn common Tropeiro objects into a display-safe DataFrame."""
    if isinstance(value, pd.DataFrame):
        return value.copy()
    if value is None:
        return pd.DataFrame()
    if isinstance(value, dict):
        if not value:
            return pd.DataFrame()
        if all(isinstance(v, dict) for v in value.values()):
            df = pd.DataFrame.from_dict(value, orient="index")
            df.index.name = "key"
            return df.reset_index()
        return pd.DataFrame([value])
    if isinstance(value, (list, tuple, set)):
        rows = list(value)
        if not rows:
            return pd.DataFrame()
        if all(isinstance(x, dict) for x in rows):
            return pd.DataFrame(rows)
        return pd.DataFrame({"value": rows})
    return pd.DataFrame([{"value": value}])


def _feature_status(ns, flag_name=None, data_name=None, always=False):
    enabled = True if always else bool(_ns_get(ns, flag_name, False))
    if not enabled:
        return "DISABLED"
    if data_name and data_name not in ns:
        return "NOT_RUN"
    return "ACTIVE"


def build_feature_matrix(ns: Mapping[str, Any]):
    hist_enabled = bool(_ns_get(ns,"ENABLE_WAYBACK",False)) or bool(_ns_get(ns,"ENABLE_COMMONCRAWL",False))
    hist_seen = "WAYBACK_ROWS" in ns or "COMMONCRAWL_ROWS" in ns
    return [
        {"feature":"multi_ioc_ingestion","status":"ACTIVE" if "INVENTORY" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"INVENTORY",[]))},
        {"feature":"dns","status":_feature_status(ns,"ENABLE_DNS","DNS_DATA"),"evidence":safe_len(_ns_get(ns,"DNS_DATA",{}))},
        {"feature":"rdap","status":_feature_status(ns,"ENABLE_RDAP","RDAP_DATA"),"evidence":safe_len(_ns_get(ns,"RDAP_DATA",{}))},
        {"feature":"certificate_transparency","status":_feature_status(ns,"ENABLE_CT","CT_DATA"),"evidence":safe_len(_ns_get(ns,"CT_DATA",{}))},
        {"feature":"historical_web","status":"ACTIVE" if hist_enabled and hist_seen else ("DISABLED" if not hist_enabled else "NOT_RUN"),"evidence":safe_len(_ns_get(ns,"WAYBACK_ROWS",[]))+safe_len(_ns_get(ns,"COMMONCRAWL_ROWS",[]))},
        {"feature":"domain_similarity","status":_feature_status(ns,"ENABLE_DOMAIN_SIMILARITY","DOMAIN_SIMILARITY"),"evidence":safe_len(_ns_get(ns,"DOMAIN_SIMILARITY",[]))},
        {"feature":"durable_identifiers","status":"ACTIVE" if "DURABLE_ROWS" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"DURABLE_ROWS",[]))},
        {"feature":"source_independence","status":"ACTIVE" if "SOURCE_INDEPENDENCE" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"SOURCE_INDEPENDENCE",[]))},
        {"feature":"cluster_guard","status":"ACTIVE" if "CAMPAIGN_CLUSTERS" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"CAMPAIGN_CLUSTERS",[]))},
        {"feature":"negative_evidence","status":"ACTIVE" if "NEGATIVE_EVIDENCE" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"NEGATIVE_EVIDENCE",[]))},
        {"feature":"attribution_ach","status":"ACTIVE" if "ATTRIBUTIONS" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"ATTRIBUTIONS",[]))},
        {"feature":"passive_takeover","status":_feature_status(ns,"ENABLE_PASSIVE_TAKEOVER","TAKEOVER_EXPOSURE"),"evidence":safe_len(_ns_get(ns,"TAKEOVER_EXPOSURE",[]))},
        {"feature":"ioc_decisioning","status":"ACTIVE" if "IOC_DECISIONS" in ns else "NOT_RUN","evidence":safe_len(_ns_get(ns,"IOC_DECISIONS",[]))},
        {"feature":"report_backend","status":"READY","evidence":0},
    ]


def report_preflight(ns: Mapping[str, Any]):
    critical=[]
    optional=[]
    for name in ("CASE_ID","WORKSPACE"):
        if name not in ns:
            critical.append(name)
    for name in (
        "INTEL_BRIEF","EXECUTIVE_ASSESSMENT","ACTION_MATRIX","IOC_DECISIONS",
        "COLLECTION_GAPS","PIVOTS","CONFIDENCE","VICTIMOLOGY","OBJECTIVES",
        "LIFECYCLE","CHURN","ATTRIBUTIONS","CAMPAIGN_CLUSTERS","LEDGER_DF",
        "STATUS","OWNERSHIP","RELATIONSHIP_GRAPH","DOMAIN_SIMILARITY"
    ):
        if name not in ns:
            optional.append(name)
    return {"ready":not critical,"critical_missing":critical,"optional_missing":optional,"partial_report":bool(optional)}


def _records(value: Any):
    if isinstance(value, pd.DataFrame):
        return value.to_dict("records")
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def build_report_data(ns: Mapping[str, Any], version: str="unknown"):
    feature_matrix=_ns_get(ns,"FEATURE_MATRIX",None) or build_feature_matrix(ns)
    assessment=_ns_get(ns,"EXECUTIVE_ASSESSMENT",None)
    if not isinstance(assessment,dict):
        assessment={
            "judgment":f"Case {_ns_get(ns,'CASE_ID','CASE')} · partial analytical report",
            "implication":"Some analytical modules were not executed or returned no data. Review Feature Coverage and Source Health before operational decisions.",
        }
    brief=_ns_get(ns,"INTEL_BRIEF",None)
    if not isinstance(brief,dict):
        brief={"case_id":_ns_get(ns,"CASE_ID","CASE"),"executive_assessment":assessment,"analytic_note":"Partial report assembled safely from available case objects."}
    return {
        "meta":{"case_id":_ns_get(ns,"CASE_ID","CASE"),"analyst":_ns_get(ns,"ANALYST",""),"brand":_ns_get(ns,"BRAND",""),"generated_at":datetime.now(timezone.utc).isoformat(),"tool":"Tropeiro Intel","version":version,"mode":_ns_get(ns,"MODE","PASSIVE"),"partial_report":report_preflight(ns)["partial_report"]},
        "executive_brief":brief,
        "executive_assessment":assessment,
        "action_matrix":_records(_ns_get(ns,"ACTION_MATRIX",[])),
        "ioc_decisions":_records(_ns_get(ns,"IOC_DECISIONS",[])),
        "collection_gaps":_records(_ns_get(ns,"COLLECTION_GAPS",[])),
        "next_best_pivots":_records(_ns_get(ns,"PIVOTS",[])),
        "confidence":_ns_get(ns,"CONFIDENCE",{}),
        "victimology":_ns_get(ns,"VICTIMOLOGY",{}),
        "objectives":_ns_get(ns,"OBJECTIVES",{}),
        "lifecycle":_ns_get(ns,"LIFECYCLE",{"stage":"UNKNOWN","reason":"Lifecycle module not run."}),
        "infrastructure_churn":_ns_get(ns,"CHURN",{}),
        "attribution_assessments":_records(_ns_get(ns,"ATTRIBUTIONS",[])),
        "attribution_ladder":_records(_ns_get(ns,"ATTRIBUTION_LADDER",[])),
        "campaign_clusters":_records(_ns_get(ns,"CAMPAIGN_CLUSTERS",[])),
        "campaign_fingerprints":_records(_ns_get(ns,"CAMPAIGN_FINGERPRINTS",[])),
        "operator_fingerprints":_records(_ns_get(ns,"OPERATOR_FINGERPRINTS",[])),
        "evidence_ledger":_records(_ns_get(ns,"LEDGER_DF",[])),
        "source_status":_records(_ns_get(ns,"STATUS",[])),
        "source_independence":_records(_ns_get(ns,"SOURCE_INDEPENDENCE",[])),
        "provider_plan":_records(_ns_get(ns,"PROVIDER_PLAN",[])),
        "ownership":_ns_get(ns,"OWNERSHIP",{}),
        "relationship_graph":_ns_get(ns,"RELATIONSHIP_GRAPH",{"nodes":[],"edges":[]}),
        "domain_similarity":_records(_ns_get(ns,"DOMAIN_SIMILARITY",[])),
        "durable_identifiers":_records(_ns_get(ns,"DURABLE_ROWS",[])),
        "web_fingerprints":_records(_ns_get(ns,"WEB_FP_ROWS",[])),
        "negative_evidence":_records(_ns_get(ns,"NEGATIVE_EVIDENCE",[])),
        "timeline":_records(_ns_get(ns,"TIMELINE",[])),
        "takeover_exposure":_records(_ns_get(ns,"TAKEOVER_EXPOSURE",[])),
        "detection_package":_ns_get(ns,"DETECTION_PACKAGE",{}),
        "feature_matrix":feature_matrix,
        "ai_entities":_records(_ns_get(ns,"AI_ENTITIES",[])),
        "ai_analysis":_ns_get(ns,"AI_ANALYSIS",{}),
        "ai_metadata":_ns_get(ns,"AI_METADATA",{}),
        "ai_evidence_packet":_ns_get(ns,"AI_EVIDENCE_PACKET_META",{}),
    }

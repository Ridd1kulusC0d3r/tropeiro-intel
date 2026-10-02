from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

SCHEMA_VERSION = 1

ARTIFACT_WEIGHTS = {
    "hash": 1.00,
    "tracker": 0.98,
    "public_email": 0.98,
    "public_phone": 0.98,
    "registrant_org": 0.92,
    "web_fingerprint": 0.88,
    "campaign_fingerprint": 0.86,
    "operator_fingerprint": 0.86,
    "url": 0.82,
    "certificate": 0.78,
    "certificate_name": 0.62,
    "domain": 0.72,
    "cname": 0.58,
    "mx": 0.48,
    "nameserver": 0.44,
    "ip": 0.28,
    "asn": 0.22,
    "registrar": 0.18,
    "provider": 0.12,
}

COMMON_INFRA_TYPES = {"ip", "asn", "registrar", "provider"}


def default_memory_path() -> Path:
    env = os.getenv("TROPEIRO_MEMORY_PATH", "").strip()
    if env:
        return Path(env).expanduser()
    if Path("/content").exists():
        return Path("/content/tropeiro_case_memory.sqlite")
    return Path.home() / ".tropeiro" / "tropeiro_case_memory.sqlite"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def normalize_artifact(kind: str, value: Any) -> str:
    kind = str(kind or "artifact").strip().lower()
    v = str(value or "").strip()
    if not v:
        return ""
    if kind in {
        "domain", "certificate_name", "cname", "mx", "nameserver",
        "registrar", "registrant_org", "provider", "tracker", "public_email"
    }:
        v = v.casefold().rstrip(".")
    if kind == "public_phone":
        v = re.sub(r"\D", "", v)
    if kind == "ip":
        try:
            v = str(ipaddress.ip_address(v))
        except ValueError:
            pass
    if kind == "hash":
        v = v.casefold()
    return v


def _add(out: Dict[Tuple[str, str], Dict[str, Any]], kind: str, value: Any, source: str, weight: Optional[float] = None):
    normalized = normalize_artifact(kind, value)
    if not normalized:
        return
    key = (kind, normalized)
    item = out.setdefault(
        key,
        {
            "artifact_type": kind,
            "value": str(value),
            "normalized_value": normalized,
            "weight": float(weight if weight is not None else ARTIFACT_WEIGHTS.get(kind, .35)),
            "sources": set(),
        },
    )
    item["sources"].add(str(source or "unknown"))


def _durable_kind(row: Mapping[str, Any]) -> str:
    raw = str(row.get("kind") or row.get("type") or row.get("label") or row.get("name") or "").casefold()
    if any(x in raw for x in ("tracker", "analytics", "gtm", "pixel", "adsense", "statcounter")):
        return "tracker"
    if any(x in raw for x in ("favicon", "html", "template", "dom", "js", "web", "fingerprint")):
        return "web_fingerprint"
    return "tracker" if raw else "web_fingerprint"


def extract_case_artifacts(report_data: Mapping[str, Any]) -> List[Dict[str, Any]]:
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for row in report_data.get("ioc_decisions", []) or []:
        if not isinstance(row, dict):
            continue
        value = row.get("ioc") or row.get("value")
        typ = str(row.get("ioc_type") or row.get("type") or "").lower()
        mapped = {"email": "public_email", "phone": "public_phone"}.get(typ, typ)
        if mapped in ARTIFACT_WEIGHTS:
            _add(out, mapped, value, "ioc_decisions")

    ownership = report_data.get("ownership", {}) or {}
    if isinstance(ownership, dict):
        for domain, data in ownership.items():
            _add(out, "domain", domain, "ownership")
            if not isinstance(data, dict):
                continue
            rd = data.get("rdap", {}) or {}
            for org in rd.get("registrant_orgs", []) or []:
                _add(out, "registrant_org", org, "rdap")
            for reg in rd.get("registrar_orgs", []) or []:
                _add(out, "registrar", reg, "rdap")
            if rd.get("registrar"):
                _add(out, "registrar", rd.get("registrar"), "rdap")
            dns = data.get("dns", {}) or {}
            for value in dns.get("A", []) or []:
                _add(out, "ip", value, "dns:A")
            for value in dns.get("AAAA", []) or []:
                _add(out, "ip", value, "dns:AAAA")
            for value in dns.get("CNAME", []) or []:
                _add(out, "cname", value, "dns:CNAME")
            for value in dns.get("MX", []) or []:
                _add(out, "mx", value, "dns:MX")
            for value in dns.get("NS", []) or []:
                _add(out, "nameserver", value, "dns:NS")
            for value in data.get("cert_names", []) or []:
                _add(out, "certificate_name", value, "crt.sh")

    for row in report_data.get("durable_identifiers", []) or []:
        if not isinstance(row, dict):
            continue
        kind = _durable_kind(row)
        value = row.get("value") or row.get("id") or row.get("identifier") or row.get("hash")
        _add(out, kind, value, "durable_identifiers")

    for row in report_data.get("web_fingerprints", []) or []:
        if not isinstance(row, dict):
            continue
        value = row.get("fingerprint") or row.get("sha256") or row.get("hash")
        if not value:
            filtered = {k: v for k, v in row.items() if k not in {"source", "timestamp", "first_seen", "last_seen"}}
            if filtered:
                value = _sha(filtered)
        _add(out, "web_fingerprint", value, "web_fingerprints")

    for row in report_data.get("campaign_fingerprints", []) or []:
        if isinstance(row, dict):
            _add(out, "campaign_fingerprint", row.get("sha256") or row.get("fingerprint") or _sha(row), "campaign_fingerprints")

    for row in report_data.get("operator_fingerprints", []) or []:
        if isinstance(row, dict):
            _add(out, "operator_fingerprint", row.get("sha256") or row.get("fingerprint") or _sha(row), "operator_fingerprints")

    for row in report_data.get("ai_entities", []) or []:
        if not isinstance(row, dict) or not row.get("analyst_confirmed"):
            continue
        label = str(row.get("label", "")).casefold()
        value = row.get("value")
        if "email" in label:
            _add(out, "public_email", value, "ai_confirmed")
        elif "phone" in label:
            _add(out, "public_phone", value, "ai_confirmed")
        elif "domain" in label:
            _add(out, "domain", value, "ai_confirmed")

    rows = []
    for item in out.values():
        item = dict(item)
        item["sources"] = sorted(item["sources"])
        rows.append(item)
    return sorted(rows, key=lambda x: (x["artifact_type"], x["normalized_value"]))


class CaseMemory:
    def __init__(self, path: Optional[str | Path] = None):
        self.path = Path(path or default_memory_path()).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self):
        con = sqlite3.connect(str(self.path))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_schema(self):
        with self.connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases(
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tool_version TEXT,
                    analyst TEXT,
                    brand TEXT,
                    mode TEXT,
                    report_sha256 TEXT NOT NULL,
                    report_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS case_artifacts(
                    case_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    normalized_value TEXT NOT NULL,
                    raw_value TEXT,
                    weight REAL NOT NULL,
                    sources_json TEXT NOT NULL,
                    PRIMARY KEY(case_id,artifact_type,normalized_value),
                    FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_artifact_lookup
                  ON case_artifacts(artifact_type,normalized_value);
                """
            )
            con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def store_case(self, report_data: Mapping[str, Any]) -> Dict[str, Any]:
        meta = report_data.get("meta", {}) or {}
        case_id = str(meta.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("case_id is required for Campaign Memory")
        report_json = _stable_json(report_data)
        report_sha = hashlib.sha256(report_json.encode("utf-8")).hexdigest()
        artifacts = extract_case_artifacts(report_data)
        now = _now()
        with self.connect() as con:
            old = con.execute("SELECT created_at FROM cases WHERE case_id=?", (case_id,)).fetchone()
            created = old["created_at"] if old else now
            con.execute(
                """
                INSERT INTO cases(case_id,created_at,updated_at,tool_version,analyst,brand,mode,report_sha256,report_json)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(case_id) DO UPDATE SET
                    updated_at=excluded.updated_at,tool_version=excluded.tool_version,
                    analyst=excluded.analyst,brand=excluded.brand,mode=excluded.mode,
                    report_sha256=excluded.report_sha256,report_json=excluded.report_json
                """,
                (
                    case_id, created, now, str(meta.get("version", "")), str(meta.get("analyst", "")),
                    str(meta.get("brand", "")), str(meta.get("mode", "")), report_sha, report_json
                ),
            )
            con.execute("DELETE FROM case_artifacts WHERE case_id=?", (case_id,))
            con.executemany(
                """
                INSERT INTO case_artifacts(case_id,artifact_type,normalized_value,raw_value,weight,sources_json)
                VALUES(?,?,?,?,?,?)
                """,
                [
                    (
                        case_id, a["artifact_type"], a["normalized_value"], a["value"],
                        a["weight"], json.dumps(a["sources"], ensure_ascii=False)
                    )
                    for a in artifacts
                ],
            )
        return {"case_id": case_id, "artifacts": len(artifacts), "report_sha256": report_sha, "memory_path": str(self.path)}

    def lure_texts(self, exclude_case_id: Optional[str] = None, limit: int = 500) -> Dict[str, str]:
        """Textos de isca guardados (`report_data['lure_text']`) dos casos mais recentes, para comparar iscas entre casos."""
        out: Dict[str, str] = {}
        with self.connect() as con:
            rows = con.execute("SELECT case_id,report_json FROM cases WHERE case_id<>? ORDER BY updated_at DESC LIMIT ?", (exclude_case_id or "", int(limit))).fetchall()
        for row in rows:
            try:
                text = json.loads(row["report_json"]).get("lure_text")
            except (ValueError, AttributeError):
                continue
            if text:
                out[row["case_id"]] = str(text)
        return out

    def list_cases(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT c.case_id,c.created_at,c.updated_at,c.tool_version,c.analyst,c.brand,c.mode,
                       COUNT(a.normalized_value) artifact_count
                FROM cases c LEFT JOIN case_artifacts a ON a.case_id=c.case_id
                GROUP BY c.case_id ORDER BY c.updated_at DESC LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict[str, Any]:
        with self.connect() as con:
            cases = con.execute("SELECT COUNT(*) n FROM cases").fetchone()["n"]
            artifacts = con.execute("SELECT COUNT(*) n FROM case_artifacts").fetchone()["n"]
            distinct = con.execute(
                "SELECT COUNT(*) n FROM (SELECT DISTINCT artifact_type,normalized_value FROM case_artifacts)"
            ).fetchone()["n"]
            last = con.execute("SELECT MAX(updated_at) x FROM cases").fetchone()["x"]
        return {
            "cases": cases, "artifact_rows": artifacts, "distinct_artifacts": distinct,
            "last_updated": last, "path": str(self.path), "schema_version": SCHEMA_VERSION
        }

    def _case_artifacts(self, case_id: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM case_artifacts WHERE case_id=?", (case_id,)).fetchall()
        return {(r["artifact_type"], r["normalized_value"]): dict(r) for r in rows}

    def _document_frequency(self, keys: Iterable[Tuple[str, str]], exclude_case_id: Optional[str] = None) -> Dict[Tuple[str, str], int]:
        result = {}
        with self.connect() as con:
            for typ, val in keys:
                if exclude_case_id:
                    row = con.execute(
                        "SELECT COUNT(DISTINCT case_id) n FROM case_artifacts WHERE artifact_type=? AND normalized_value=? AND case_id<>?",
                        (typ, val, exclude_case_id),
                    ).fetchone()
                else:
                    row = con.execute(
                        "SELECT COUNT(DISTINCT case_id) n FROM case_artifacts WHERE artifact_type=? AND normalized_value=?",
                        (typ, val),
                    ).fetchone()
                result[(typ, val)] = int(row["n"] or 0)
        return result

    def prevalence_for_report(self, report_data: Mapping[str, Any], exclude_case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        artifacts = extract_case_artifacts(report_data)
        keys = [(a["artifact_type"], a["normalized_value"]) for a in artifacts]
        dfs = self._document_frequency(keys, exclude_case_id)
        with self.connect() as con:
            if exclude_case_id:
                total = con.execute("SELECT COUNT(*) n FROM cases WHERE case_id<>?", (exclude_case_id,)).fetchone()["n"]
            else:
                total = con.execute("SELECT COUNT(*) n FROM cases").fetchone()["n"]
        rows = []
        for a in artifacts:
            key = (a["artifact_type"], a["normalized_value"])
            df = dfs.get(key, 0)
            prevalence = (df / total) if total else 0.0
            rarity = (math.log((total + 1) / (df + 1)) / math.log(total + 1)) if total > 0 else 1.0
            rows.append(
                {
                    "artifact_type": a["artifact_type"], "value": a["value"], "case_frequency": df,
                    "memory_cases": total, "prevalence": round(prevalence, 4), "rarity": round(rarity, 4),
                    "base_weight": a["weight"], "sources": a["sources"]
                }
            )
        return sorted(rows, key=lambda x: (-x["rarity"], -x["base_weight"], x["artifact_type"]))

    def compare_report(self, report_data: Mapping[str, Any], exclude_case_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        current_rows = extract_case_artifacts(report_data)
        current = {(a["artifact_type"], a["normalized_value"]): a for a in current_rows}
        if not current:
            return []
        candidates = self.list_cases(limit=1000)
        results = []
        for c in candidates:
            case_id = c["case_id"]
            if exclude_case_id and case_id == exclude_case_id:
                continue
            other = self._case_artifacts(case_id)
            shared = set(current) & set(other)
            if not shared:
                continue
            union = set(current) | set(other)
            dfs = self._document_frequency(union, exclude_case_id)
            total = max(1, len([x for x in candidates if not exclude_case_id or x["case_id"] != exclude_case_id]))

            def rarity(k):
                df = dfs.get(k, 0)
                if total <= 1:
                    return 1.0 if df == 0 else .25
                return max(.0, min(1.0, math.log((total + 1) / (df + 1)) / math.log(total + 1)))

            def weight(k):
                base = float(current.get(k, other.get(k, {})).get("weight", ARTIFACT_WEIGHTS.get(k[0], .35)))
                return base * (.15 + .85 * rarity(k))

            denom = sum(weight(k) for k in union) or 1.0
            numerator = sum(weight(k) for k in shared)
            score = numerator / denom
            discriminating = sum(1 for k in shared if ARTIFACT_WEIGHTS.get(k[0], .35) >= .75)
            shared_types = {k[0] for k in shared}
            if len(shared) < 2:
                score = min(score, .29)
            if discriminating == 0:
                score = min(score, .39)
            if shared_types and shared_types.issubset(COMMON_INFRA_TYPES):
                score = min(score, .25)
            label = (
                "STRONG_SIMILARITY" if score >= .65 else
                "MODERATE_SIMILARITY" if score >= .40 else
                "WEAK_SIMILARITY" if score >= .20 else
                "LOW_SIMILARITY"
            )
            contributions = []
            for k in sorted(shared, key=lambda x: weight(x), reverse=True)[:20]:
                raw = current.get(k, {}).get("value") or other.get(k, {}).get("raw_value") or k[1]
                contributions.append(
                    {
                        "artifact_type": k[0], "value": raw, "rarity": round(rarity(k), 4),
                        "weighted_contribution": round(weight(k), 4),
                        "discriminating": ARTIFACT_WEIGHTS.get(k[0], .35) >= .75
                    }
                )
            results.append(
                {
                    "case_id": case_id, "similarity_score": round(score, 4), "similarity_band": label,
                    "shared_artifacts": len(shared), "shared_discriminating": discriminating,
                    "top_contributions": contributions, "same_operator_inferred": False,
                    "analytic_note": "Cross-case similarity is a lead for review, not actor/operator attribution."
                }
            )
        return sorted(
            results,
            key=lambda x: (-x["similarity_score"], -x["shared_discriminating"], -x["shared_artifacts"])
        )[: int(limit)]

    def import_case_json(self, path: str | Path) -> Dict[str, Any]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.store_case(data)

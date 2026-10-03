from __future__ import annotations

import ipaddress
import re
from typing import Dict, List

TYPE_LABELS = {
    "AUTO": "Alvo da investigação",
    "DOMAIN": "Domínio",
    "URL": "URL / link",
    "IP": "Endereço IP",
    "EMAIL": "E-mail / conta observada",
    "HASH": "Hash de arquivo",
    "PHONE": "Telefone observado",
    "MULTI_IOC": "Vários IOCs",
    "LURE_TEXT": "Texto da isca / mensagem",
}

TYPE_PLACEHOLDERS = {
    "AUTO": "Cole um domínio, URL, IP, e-mail, hash, telefone ou texto. O Tropeiro tenta identificar o tipo.",
    "DOMAIN": "ex.: dominio-suspeito.com",
    "URL": "ex.: https://dominio-suspeito.com/login",
    "IP": "ex.: 203.0.113.10",
    "EMAIL": "ex.: contato@dominio-suspeito.com",
    "HASH": "ex.: SHA256 / SHA1 / MD5 observado em telemetria autorizada",
    "PHONE": "ex.: +55 31 99999-9999",
    "MULTI_IOC": "Cole um IOC por linha: domínio, URL, IP, hash, e-mail...",
    "LURE_TEXT": "Cole a mensagem recebida, sem inserir senhas ou dados pessoais desnecessários.",
}

SUPPORT_NOTES = {
    "DOMAIN": "Fluxo automatizado completo: DNS, RDAP, CT, histórico, urlscan, lookalikes, correlação e relatório.",
    "URL": "Fluxo automatizado completo. O domínio é extraído da URL e os módulos web recebem prioridade.",
    "IP": "O IP é preservado no caso e usado para correlação. Módulos exclusivamente de domínio são ignorados quando não houver domínio relacionado.",
    "EMAIL": "Usado como IOC/correlação em investigação defensiva. O Tropeiro não tenta descobrir dados privados do dono da conta.",
    "HASH": "Usado para correlação e inteligência de ameaças quando providers compatíveis estiverem habilitados.",
    "PHONE": "Usado como IOC/correlação quando já observado no caso. Não é um mecanismo de busca de dados privados de pessoas.",
    "MULTI_IOC": "O Tropeiro separa os tipos encontrados e aplica as rotas compatíveis com cada IOC.",
    "LURE_TEXT": "Extrai IOCs do texto e alimenta victimology/objective. Não envie senhas, tokens ou dados pessoais desnecessários.",
    "AUTO": "O tipo será detectado automaticamente a partir do conteúdo.",
}

def detect_input_type(text: str) -> str:
    """Detecta o tipo do alvo (regras em `tropeiro.targets.classify`)."""
    from .targets import classify
    return classify(text)

def input_label(kind: str) -> str:
    return TYPE_LABELS.get((kind or "AUTO").upper(), TYPE_LABELS["AUTO"])

def input_placeholder(kind: str) -> str:
    return TYPE_PLACEHOLDERS.get((kind or "AUTO").upper(), TYPE_PLACEHOLDERS["AUTO"])

def support_note(kind: str) -> str:
    return SUPPORT_NOTES.get((kind or "AUTO").upper(), SUPPORT_NOTES["AUTO"])

def requirements_for_input(kind: str, has_brand: bool = False, has_lure: bool = False) -> List[str]:
    kind = (kind or "AUTO").upper()
    req = set()
    if kind in {"DOMAIN", "URL", "MULTI_IOC", "AUTO"}:
        req |= {"dns","registration","ownership","tls","historical_web","web_scan","redirects","threat_intel","relationships","asn"}
    elif kind == "IP":
        req |= {"infrastructure","asn","threat_intel","relationships"}
    elif kind == "HASH":
        req |= {"threat_intel","relationships"}
    elif kind in {"EMAIL","PHONE","LURE_TEXT"}:
        req |= {"relationships"}
    if has_brand:
        req |= {"subdomains","historical_web","web_scan"}
    if has_lure:
        req |= {"web_scan","relationships"}
    return sorted(req)

def recommended_features(kind: str, mode: str = "PASSIVE", budget: str = "balanced",
                         secrets: Dict[str, str] | None = None, has_brand: bool = False) -> Dict[str, bool]:
    kind = (kind or "AUTO").upper()
    secrets = secrets or {}
    domainish = kind in {"DOMAIN","URL","MULTI_IOC","AUTO"}
    urlish = kind in {"URL","MULTI_IOC"}
    features = {
        "ENABLE_DNS": domainish,
        "ENABLE_RDAP": domainish,
        "ENABLE_CT": domainish,
        "ENABLE_WAYBACK": domainish,
        "ENABLE_COMMONCRAWL": False,
        "ENABLE_URLSCAN": domainish,
        "ENABLE_URLSCAN_DETAILS": urlish or domainish,
        "ENABLE_OTX": domainish,
        "ENABLE_VT": bool(secrets.get("VT_API_KEY")) and kind in {"DOMAIN","URL","IP","HASH","MULTI_IOC"},
        "ENABLE_THREATFOX": bool(secrets.get("THREATFOX_AUTH_KEY")) and kind in {"DOMAIN","URL","IP","HASH","MULTI_IOC"},
        "ENABLE_DNSTWIST": domainish or has_brand,
        "ENABLE_DNSDUMPSTER": bool(secrets.get("DNSDUMPSTER_API_KEY")) and domainish,
        "ENABLE_FOFA": bool(secrets.get("FOFA_API_KEY")) and domainish and budget != "free",
        "ENABLE_CENSYS": bool(secrets.get("CENSYS_PAT")) and domainish and budget != "free",
        "ENABLE_DOMAIN_SIMILARITY": domainish or has_brand,
        "ENABLE_PASSIVE_TAKEOVER": domainish,
        "ENABLE_HTTP_PROBE": False,
    }
    if mode == "SAFE_ENRICHMENT":
        features["ENABLE_COMMONCRAWL"] = domainish
    return features

def budget_limits(budget: str, target_count: int = 1) -> Dict[str, int]:
    target_count = max(1, int(target_count or 1))
    presets = {
        "free": {"DNSTWIST_MAX": 80, "URLSCAN_DETAIL_MAX": 5},
        "balanced": {"DNSTWIST_MAX": 250, "URLSCAN_DETAIL_MAX": 12},
        "extended": {"DNSTWIST_MAX": 600, "URLSCAN_DETAIL_MAX": 30},
    }
    values = dict(presets.get(budget, presets["balanced"]))
    if target_count > 10:
        values["DNSTWIST_MAX"] = max(25, values["DNSTWIST_MAX"] // target_count)
        values["URLSCAN_DETAIL_MAX"] = max(2, values["URLSCAN_DETAIL_MAX"] // min(target_count, 10))
    return values


# --- plano de fontes por tipo de alvo (usado pelo pipeline, pela CLI e pelo Workbench) -----------------------------

SOURCE_FLAGS = {          # fonte -> (flag, assunto, exige chave, só em SAFE_ENRICHMENT)
    "dns": ("ENABLE_DNS", "domain", None, False),
    "rdap": ("ENABLE_RDAP", "domain", None, False),
    "crt.sh": ("ENABLE_CT", "domain", None, False),
    "urlscan": ("ENABLE_URLSCAN", "domain", None, False),
    "otx": ("ENABLE_OTX", "domain", None, False),
    "wayback": ("ENABLE_WAYBACK", "domain", None, False),
    "commoncrawl": ("ENABLE_COMMONCRAWL", "domain", None, True),
    "virustotal": ("ENABLE_VT", "any", "VT_API_KEY", False),
    "threatfox": ("ENABLE_THREATFOX", "any", "THREATFOX_AUTH_KEY", False),
    "dns:PTR": ("ENABLE_PTR", "ip", None, False),
    "rdap_ip": ("ENABLE_RDAP_IP", "ip", None, False),
    "urlscan_ip": ("ENABLE_URLSCAN_IP", "ip", None, False),
}

def features_for_target(kinds: set, mode: str = "PASSIVE", budget: str = "balanced", secrets: Dict[str, str] | None = None) -> Dict[str, bool]:
    """Quais fontes ligar, a partir dos **tipos de assunto presentes** ({"domain","ip","hash"}), do modo e das chaves."""
    secrets = secrets or {}
    out: Dict[str, bool] = {}
    for name, (flag, subj, key, safe_only) in SOURCE_FLAGS.items():
        applies = bool(kinds) if subj == "any" else subj in kinds
        out[flag] = bool(applies and (not key or secrets.get(key)) and (not safe_only or mode == "SAFE_ENRICHMENT"))
    out["ENABLE_URLSCAN_DETAILS"] = out["ENABLE_URLSCAN"]
    return out

def skip_reason(source: str, kinds: set, mode: str, secrets: Dict[str, str] | None = None) -> tuple[str, str] | None:
    """(estado, explicação) se a fonte se aplica ao alvo mas está desligada; None se aplica e está ligada ou não se aplica."""
    secrets = secrets or {}
    flag, subj, key, safe_only = SOURCE_FLAGS[source]
    if not (bool(kinds) if subj == "any" else subj in kinds):
        return None
    if key and not secrets.get(key):
        return "SKIPPED_MISSING_SECRET", f"defina {key} para ativar (opcional)"
    if safe_only and mode != "SAFE_ENRICHMENT":
        return "SKIPPED_MODE", "só no modo SAFE_ENRICHMENT"
    return None

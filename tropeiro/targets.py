"""Alvos de investigação: classificação robusta, refang e extração.

Regra central: **um texto com palavras é uma isca**, não um telefone ou domínio, mesmo que contenha números e links.
Só vira tipo "simples" (domínio, URL, IP, e-mail, hash, telefone) o que é, por inteiro, um ou mais tokens desse tipo.
"""
from __future__ import annotations
import ipaddress, re
from dataclasses import dataclass, field
from typing import Dict, List
from .utils import extract_iocs, refang, hostname, valid_hostname
from .intelligence.legit_domains import is_known_legit

KINDS=("AUTO","DOMAIN","URL","IP","EMAIL","HASH","PHONE","MULTI_IOC","LURE_TEXT")
RE_HASH=re.compile(r"[A-Fa-f0-9]{32}|[A-Fa-f0-9]{40}|[A-Fa-f0-9]{64}")
RE_EMAIL=re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",re.I)
RE_DOMAIN=re.compile(r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}")
RE_PHONE=re.compile(r"\+?\d[\d\s().-]{8,18}\d")        # o texto INTEIRO precisa ser isto

def _token_kind(tok: str) -> str:
    if re.match(r"^https?://\S+$",tok,re.I): return "URL"
    try:
        ipaddress.ip_address(tok); return "IP"
    except ValueError: pass
    if RE_HASH.fullmatch(tok): return "HASH"
    if RE_EMAIL.fullmatch(tok): return "EMAIL"
    if RE_PHONE.fullmatch(tok) and 10<=len(re.sub(r"\D","",tok))<=15: return "PHONE"
    if RE_DOMAIN.fullmatch(tok): return "DOMAIN"
    return "LURE_TEXT"

def split_tokens(text: str):
    """Lista de tokens se o texto é só uma lista de IOCs (um por linha, ou separados por vírgula/;); senão None."""
    tokens=[]
    for line in (text or "").splitlines():
        line=line.strip()
        if not line: continue
        if RE_PHONE.fullmatch(line):                      # "+55 11 99999-0000" tem espaços mas é um token
            tokens.append(line); continue
        parts=[p.strip() for p in re.split(r"[;,]",line) if p.strip()] if (";" in line or "," in line) else [line]
        for p in parts:
            if re.search(r"\s",p) and not RE_PHONE.fullmatch(p): return None
            tokens.append(p)
    return tokens

def classify(text: str) -> str:
    """AUTO/DOMAIN/URL/IP/EMAIL/HASH/PHONE/MULTI_IOC/LURE_TEXT a partir do conteúdo."""
    value=refang(text or "").strip()
    if not value: return "AUTO"
    tokens=split_tokens(value)
    if tokens is None or not tokens: return "LURE_TEXT"
    kinds={_token_kind(t) for t in tokens}
    if "LURE_TEXT" in kinds: return "LURE_TEXT"
    return kinds.pop() if len(kinds)==1 else "MULTI_IOC"

def registrable(host: str) -> str:
    """Domínio registrável. TLDs fora da lista pública (ex.: .example, .test) usam os dois últimos rótulos."""
    h=hostname(host)
    try:
        import tldextract
        e=tldextract.extract(h)
        if e.domain and e.suffix: return f"{e.domain}.{e.suffix}"
    except Exception:
        pass
    parts=[p for p in h.split(".") if p]
    return ".".join(parts[-2:]) if len(parts)>=2 else h

@dataclass
class Target:
    raw: str
    kind: str
    text: str                                   # texto já com refang
    iocs: Dict[str,List[str]] = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)     # domínios registráveis a coletar (sem plataformas legítimas)
    ips: List[str] = field(default_factory=list)
    hashes: List[str] = field(default_factory=list)
    skipped_legit: List[str] = field(default_factory=list)
    lure_text: str = ""                         # só preenchido para LURE_TEXT / MULTI_IOC com prosa

    @property
    def kinds_present(self) -> set:
        k=set()
        if self.domains: k.add("domain")
        if self.ips: k.add("ip")
        if self.hashes: k.add("hash")
        return k

def parse_target(raw: str, selected: str="AUTO") -> Target:
    text=refang(raw or "").strip()
    sel=(selected or "AUTO").upper()
    kind=classify(text) if sel=="AUTO" else sel
    iocs={k:list(v) for k,v in extract_iocs(text).items()}
    def add(typ,val):
        if val: iocs.setdefault(typ,[]).append(val)
    if sel!="AUTO" or kind in {"DOMAIN","URL","IP","EMAIL","HASH","PHONE","MULTI_IOC"}:
        for tok in (split_tokens(text) or []):
            tk=_token_kind(tok)
            if tk=="DOMAIN": add("domain",tok.strip(".").lower())
            elif tk=="URL": add("url",tok); add("domain",hostname(tok))
            elif tk=="IP": add("ip",tok)
            elif tk=="EMAIL": add("email",tok.lower()); add("domain",tok.split("@")[-1].lower())
            elif tk=="HASH": add("hash",tok.lower())
            elif tk=="PHONE": add("phone",re.sub(r"\D","",tok))
    iocs={k:sorted(set(v)) for k,v in iocs.items() if v}
    hosts=[]
    skipped=[]
    for d in iocs.get("domain",[]):
        h=valid_hostname(d)
        if not h or "." not in h: continue
        if is_known_legit(h): skipped.append(h); continue
        hosts.append(registrable(h))
    ips=[]
    for ip in iocs.get("ip",[]):
        try:
            a=ipaddress.ip_address(ip)
            if a.is_global: ips.append(str(a))
            else: skipped.append(ip)                 # privado/reservado: nada a consultar publicamente
        except ValueError: pass
    return Target(raw=raw or "",kind=kind,text=text,iocs=iocs,domains=sorted(set(hosts)),ips=sorted(set(ips)),
                  hashes=sorted(set(iocs.get("hash",[]))),skipped_legit=sorted(set(skipped)),
                  lure_text=text if kind in {"LURE_TEXT","MULTI_IOC"} else "")

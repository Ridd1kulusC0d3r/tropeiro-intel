import re

def _escape_sigma(s): return str(s).replace("\\","\\\\").replace("'","''")

def build_detection_package(decisions, brand=None, attack_id="T1598.003"):
    domains=[d["ioc"] for d in decisions if d["ioc_type"]=="domain" and d.get("hunt_recommended")]
    urls=[d["ioc"] for d in decisions if d["ioc_type"]=="url" and d.get("hunt_recommended")]
    high_domains=[d["ioc"] for d in decisions if d["ioc_type"]=="domain" and d.get("block_recommended")]
    pkg={"attack_mapping":{"technique":attack_id,"name":"Phishing for Information: Spearphishing Link" if attack_id=="T1598.003" else "Phishing for Information","basis":"Observed phishing/link indicators; analyst must validate campaign objective."},"dns_hunt":{"domains":domains},"proxy_hunt":{"urls":urls,"domains":domains},"email_hunt":{"sender_or_link_domains":domains,"brand":brand},"identity_hunt":{"guidance":"Review authentication anomalies after observed phishing exposure; correlate only where authorized telemetry exists."},"blocklist":{"domains":high_domains},"sigma_candidate":None,"splunk_examples":[],"kql_examples":[]}
    if domains:
        sigma_vals="\n".join(f"      - '{_escape_sigma(x)}'" for x in domains[:100])
        pkg["sigma_candidate"]=f"""title: Tropeiro Intel - Phishing Domain DNS Candidate
status: experimental
logsource:
  category: dns
detection:
  selection:
    query:
{sigma_vals}
  condition: selection
falsepositives:
  - Shared or legitimate infrastructure if analyst validation is incomplete
level: high
"""
        joined=" OR ".join(f'"{x}"' for x in domains[:50]);pkg["splunk_examples"].append(f'index=dns ({joined})');pkg["kql_examples"].append("DnsEvents | where Name in~ ("+", ".join(repr(x) for x in domains[:50])+")")
    return pkg

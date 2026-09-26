def _q(s):return str(s).replace('"','\\"')

def build_detection_package(decisions,brand=None,attack_id='T1598.003'):
    domains=[d['ioc'] for d in decisions if d.get('ioc_type')=='domain' and d.get('hunt_recommended')]
    urls=[d['ioc'] for d in decisions if d.get('ioc_type')=='url' and d.get('hunt_recommended')]
    high_domains=[d['ioc'] for d in decisions if d.get('ioc_type')=='domain' and d.get('block_recommended')]
    vals=', '.join(repr(x) for x in domains[:100]); spl=' OR '.join(f'"{_q(x)}"' for x in domains[:50])
    sigma=None
    if domains:
        lines='\n'.join(f"      - '{x.replace(chr(39), chr(39)*2)}'" for x in domains[:100])
        sigma=f"""title: Tropeiro Intel Phishing Domain Candidate\nstatus: experimental\nlogsource:\n  category: dns\ndetection:\n  selection:\n    query:\n{lines}\n  condition: selection\nfalsepositives:\n  - Shared or legitimate infrastructure without analyst validation\nlevel: high\n"""
    return {
      'attack_mapping':{'technique':attack_id,'name':'Phishing for Information: Spearphishing Link','basis':'Descriptive mapping only; analyst validation required.'},
      'dns_hunt':{'domains':domains},'proxy_hunt':{'urls':urls,'domains':domains},'email_hunt':{'sender_or_link_domains':domains,'brand':brand},
      'identity_hunt':{'guidance':'Correlate authentication anomalies only in authorized telemetry after suspected phishing exposure.'},
      'blocklist':{'domains':high_domains},'sigma_candidate':sigma,
      'splunk':f'index=dns ({spl})' if domains else '',
      'sentinel_kql':f'DnsEvents | where Name in~ ({vals})' if domains else '',
      'elastic_esql':f'FROM dns-* | WHERE dns.question.name IN ({vals})' if domains else '',
      'wazuh_query':{'field':'data.dns.question.name','values':domains[:100]},
      'suricata_candidates':[f'alert dns any any -> any any (msg:"Tropeiro Intel phishing domain"; dns.query; content:"{x}"; nocase; sid:{9000000+i}; rev:1;)' for i,x in enumerate(high_domains[:50],1)],
      'note':'Generated detections are candidates and require local schema/rule validation.'
    }

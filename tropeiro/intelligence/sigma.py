"""Gera regra Sigma (YAML) a partir de IOCs; o Sigma converte para Elastic, Wazuh, Splunk etc."""
import uuid
from datetime import date
from ..utils import valid_hostname

NS=uuid.UUID('7b1d2f4a-0c5e-4a9b-9d3e-5a6f1c2b8e01')

def _q(v): return "'"+str(v).replace("'","''")+"'"

def _rule(title,case_id,category,field_lines,desc,extra=None,condition='selection'):
    rid=uuid.uuid5(NS,f'sigma:{case_id}:{category}')
    return '\n'.join([f'title: {_q(title)}',f'id: {rid}','status: experimental',f'description: {_q(desc)}',
        'author: Tropeiro Intel',f'date: {date.today():%Y/%m/%d}','logsource:',f'  category: {category}',
        'detection:','  selection:',*field_lines,*(extra or []),f'  condition: {condition}',
        'falsepositives:','  - Revisar o contexto antes de bloquear: IOC pode ter sido reaproveitado','level: medium','tags:','  - attack.initial_access','  - attack.t1566'])

def sigma_rules(iocs,case_id):
    """Retorna {'dns': yaml, 'network': yaml} só para o que existir. Domínios inválidos são descartados."""
    out={}
    doms=sorted({d for d in map(valid_hostname,iocs.get('domain',[])) if d})
    if doms:
        out['dns']=_rule(f'Tropeiro {case_id}: consultas DNS a domínios da campanha',case_id,'dns',
                         ['    query:',*[f'      - {_q(d)}' for d in doms]],
                         'Domínios observados na investigação de phishing (igualdade exata ou subdomínio)',
                         extra=['  selection_sub:','    query|endswith:',*[f'      - {_q("."+d)}' for d in doms]],
                         condition='selection or selection_sub')
    ips=sorted(set(iocs.get('ip',[])))
    if ips:
        out['network']=_rule(f'Tropeiro {case_id}: conexões a IPs da campanha',case_id,'firewall',
                             ['    dst_ip:',*[f'      - {_q(i)}' for i in ips]],'IPs observados na investigação de phishing')
    return out

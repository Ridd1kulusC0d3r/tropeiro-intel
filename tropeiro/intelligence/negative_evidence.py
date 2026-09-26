def evaluate_negative_evidence(context):
    """Represent absences explicitly without treating missing data as proof."""
    rows=[]
    def add(signal,kind,impact,interpretation,confidence='LOW'):
        rows.append({'signal':signal,'absence_type':kind,'impact':impact,'interpretation':interpretation,'confidence':confidence})
    if context.get('rdap_privacy_proxy'):
        add('public_registrant_missing','expected_absence','none','Privacy/proxy registration makes missing public registrant expected.')
    elif context.get('rdap_checked') and not context.get('registrant_org_present'):
        add('public_registrant_missing','natural_absence','low','No public registrant organization was observed; this does not imply concealment.')
    if context.get('historical_scan_expected') and context.get('historical_scan_count',0)==0:
        add('historical_web_absent','suspicious_absence','medium','No indexed historical web artifact was found where coverage was expected; verify source coverage before inference.')
    if context.get('expected_mx') and not context.get('mx_present'):
        add('mx_absent','natural_absence','low','No MX record observed; may be normal for a web-only lure domain.')
    if context.get('prior_campaign_tracker') and not context.get('tracker_reused'):
        add('tracker_not_reused','expected_absence','medium','A previously durable tracker was not observed; this weakens, but does not refute, same-operator hypothesis.','MODERATE')
    return rows

SUPPORT = {
    "same_phone":{"H1_same_operator":3,"H2_shared_kit":0,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-2},
    "same_email":{"H1_same_operator":3,"H2_shared_kit":0,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-2},
    "same_tracker":{"H1_same_operator":3,"H2_shared_kit":1,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-2},
    "same_registrant_org":{"H1_same_operator":3,"H2_shared_kit":0,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-2},
    "same_certificate":{"H1_same_operator":2,"H2_shared_kit":1,"H3_shared_hosting":0,"H4_reseller":1,"H5_coincidence":-1},
    "same_redirect_chain":{"H1_same_operator":2,"H2_shared_kit":2,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-1},
    "same_html_fingerprint":{"H1_same_operator":1,"H2_shared_kit":3,"H3_shared_hosting":0,"H4_reseller":0,"H5_coincidence":-1},
    "same_jarm":{"H1_same_operator":1,"H2_shared_kit":0,"H3_shared_hosting":2,"H4_reseller":1,"H5_coincidence":0},
    "same_ns_pair":{"H1_same_operator":1,"H2_shared_kit":0,"H3_shared_hosting":2,"H4_reseller":2,"H5_coincidence":0},
    "same_mx":{"H1_same_operator":1,"H2_shared_kit":0,"H3_shared_hosting":1,"H4_reseller":1,"H5_coincidence":0},
    "same_ip":{"H1_same_operator":1,"H2_shared_kit":0,"H3_shared_hosting":3,"H4_reseller":2,"H5_coincidence":1},
    "same_asn":{"H1_same_operator":0,"H2_shared_kit":0,"H3_shared_hosting":3,"H4_reseller":2,"H5_coincidence":1},
    "same_provider":{"H1_same_operator":0,"H2_shared_kit":0,"H3_shared_hosting":3,"H4_reseller":2,"H5_coincidence":1},
}

def assess_hypotheses(evidence_codes):
    scores = {h:0 for h in next(iter(SUPPORT.values())).keys()}
    used = []
    for code in evidence_codes:
        if code not in SUPPORT: continue
        used.append(code)
        for h,v in SUPPORT[code].items(): scores[h] += v
    ranked = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    return {"scores":scores,"ranking":ranked,"evidence_used":used}

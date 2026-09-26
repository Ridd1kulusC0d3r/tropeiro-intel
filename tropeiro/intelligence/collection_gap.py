def build_collection_gaps(context):
    gaps=[]
    def add(gap,priority,impact,collection,expected_value="MEDIUM"):
        gaps.append({"gap":gap,"priority":priority,"impact":impact,"recommended_collection":collection,"expected_value":expected_value})
    if not context.get("active_state_known"):
        add("campaign_activity_status","P1","Cannot safely decide whether blocking/takedown remains urgent.","Revalidate DNS, latest urlscan sightings, passive TI and last_seen.","HIGH")
    if not context.get("registration_entity_known"):
        add("registration_entity","P2","Weakens ownership and takedown routing.","RDAP public entities; historical registration source where legally available.","HIGH")
    if not context.get("redirect_chain_known"):
        add("redirect_chain","P1","May hide durable redirectors and credential destination.","urlscan Result API redirects and historical scans.","HIGH")
    if not context.get("credential_endpoint_known"):
        add("credential_destination","P1","Cannot determine whether campaign still collects credentials or where data is sent.","Third-party sandbox/public scan artifacts; avoid interacting with live forms.","HIGH")
    if not context.get("victimology_known"):
        add("victimology","P2","Limits prioritization and defensive communication.","Analyze lure language, impersonated brand, URL paths, page titles and reported targets.","MEDIUM")
    if not context.get("operator_identity_known"):
        add("operator_identity","P3","Actor naming is not required for immediate defense but limits strategic attribution.","Seek independent registration/TLS/tracker/contact overlaps; do not infer identity from hosting alone.","LOW")
    if int(context.get("independent_source_families",0)) < 2:
        add("source_diversity","P1","Single-source judgments are fragile.","Confirm with at least one independent source family.","HIGH")
    return gaps

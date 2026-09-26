KNOWN_SERVICE_SUFFIXES=(
    'github.io','herokudns.com','azurewebsites.net','cloudfront.net','fastly.net',
    'netlify.app','vercel.app','ghost.io','readme.io','zendesk.com','shopify.com'
)

def assess_passive_exposure(domain,cname_targets,resolver=None):
    """Passive dangling-DNS exposure signal only. Never claims or validates third-party resources."""
    rows=[]
    for target in sorted(set(cname_targets or [])):
        resolves=None
        if resolver is not None:
            try:resolves=bool(resolver(target,'A') or resolver(target,'AAAA'))
            except Exception:resolves=None
        suffix=next((x for x in KNOWN_SERVICE_SUFFIXES if str(target).lower().rstrip('.').endswith(x)),None)
        status='INSUFFICIENT'
        if resolves is False:status='POTENTIALLY_DANGLING'
        elif resolves is True:status='RESOLVES'
        rows.append({'domain':domain,'cname_target':target,'service_hint':suffix,'target_resolves':resolves,'status':status,
                     'validation':'AUTHORIZED_VALIDATION_REQUIRED' if status=='POTENTIALLY_DANGLING' else 'PASSIVE_ONLY',
                     'note':'Detection only; do not claim, register, or interact with third-party resources.'})
    return rows

import hashlib, json

def operator_fingerprint(features):
    stable={
        "registrars":sorted(set(features.get("registrars",[]))),
        "registrant_orgs":sorted(set(features.get("registrant_orgs",[]))),
        "nameservers":sorted(set(features.get("nameservers",[]))),
        "mx":sorted(set(features.get("mx",[]))),
        "certificates":sorted(set(features.get("certificates",[]))),
        "trackers":sorted(set(features.get("trackers",[]))),
        "jarm":sorted(set(features.get("jarm",[]))),
        "redirect_fingerprints":sorted(set(features.get("redirect_fingerprints",[]))),
        "template_hashes":sorted(set(features.get("template_hashes",[]))),
        "registration_hours_utc":sorted(set(features.get("registration_hours_utc",[]))),
    }
    raw=json.dumps(stable,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
    stable["sha256"]=hashlib.sha256(raw).hexdigest()
    return stable

from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Settings:
    case_id: str = "TI-001"
    analyst: str = "Analista"
    brand: str = ""
    workspace: Path = Path("/content/tropeiro_workspace")
    cache_ttl_seconds: int = 3600
    enable_http_probe: bool = False
    urlscan_api_key: str = ""
    vt_api_key: str = ""
    threatfox_auth_key: str = ""
    phishtank_app_key: str = ""
    dnsdumpster_api_key: str = ""
    fofa_api_key: str = ""
    censys_pat: str = ""
    censys_organization_id: str = ""
    source_reliability: dict = field(default_factory=lambda: {"manual/input": .90,"dns": .95,"rdap": .95,"crt.sh": .90,"wayback": .85,"commoncrawl": .80,"urlscan": .90,"otx": .70,"virustotal": .85,"threatfox": .85,"urlhaus": .85,"phishtank": .80,"openphish": .80,"dnstwist": .75,"dnsdumpster": .85,"fofa": .85,"censys": .90,"derived": .60})

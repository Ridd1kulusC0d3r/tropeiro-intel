from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import hashlib,json

def now_iso():return datetime.now(timezone.utc).isoformat()
def canonical_json(obj):return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def digest(obj):return hashlib.sha256(canonical_json(obj).encode()).hexdigest()
@dataclass(frozen=True)
class Observation:
    entity:str;entity_type:str;source:str;value:str;observed_at:str=field(default_factory=now_iso);confidence:str="observed";notes:str=""
    def evidence_id(self):return "ev-"+digest(asdict(self))[:16]
@dataclass
class Finding:
    kind:str;value:str;source:str;seed:str;confidence:str="candidate";notes:str="";observed_at:str=field(default_factory=now_iso)

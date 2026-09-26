import json, time, hashlib
from pathlib import Path
class FileCache:
    def __init__(self,path,ttl=3600): self.path=Path(path); self.path.mkdir(parents=True,exist_ok=True); self.ttl=ttl
    def _p(self,key): return self.path/(hashlib.sha256(key.encode()).hexdigest()+'.json')
    def get(self,key):
        p=self._p(key)
        if not p.exists() or time.time()-p.stat().st_mtime > self.ttl: return None
        try: return json.loads(p.read_text())
        except Exception: return None
    def set(self,key,value): self._p(key).write_text(json.dumps(value,ensure_ascii=False)); return value

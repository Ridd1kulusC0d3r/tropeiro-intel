import sqlite3, json
from pathlib import Path
class CaseStore:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path)
        self.db.execute('create table if not exists observations (case_id text,evidence_id text primary key,entity text,entity_type text,source text,value text,observed_at text,confidence text,notes text)')
        self.db.execute('create table if not exists snapshots (case_id text,created_at text,payload text)')
    def add_observation(self,case_id,o):
        self.db.execute('insert or ignore into observations values (?,?,?,?,?,?,?,?,?)',(case_id,o.evidence_id(),o.entity,o.entity_type,o.source,o.value,o.observed_at,o.confidence,o.notes)); self.db.commit()
    def save_snapshot(self,case_id,created_at,payload): self.db.execute('insert into snapshots values (?,?,?)',(case_id,created_at,json.dumps(payload,ensure_ascii=False))); self.db.commit()

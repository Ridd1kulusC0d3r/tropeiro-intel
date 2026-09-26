import pandas as pd
from dataclasses import asdict

def reliability(source,matrix):
    if source in matrix:return matrix[source]
    return matrix.get(source.split(':')[0],.50)

def build(observations,matrix):
    rows=[]
    for o in observations:
        d=asdict(o);rows.append({'evidence_id':o.evidence_id(),**d,'source_reliability':reliability(o.source,matrix),'derived':o.confidence=='derived'})
    return pd.DataFrame(rows).drop_duplicates('evidence_id') if rows else pd.DataFrame()

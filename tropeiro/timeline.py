def build_timeline(ledger_df):
    if ledger_df is None or ledger_df.empty: return []
    cols=[c for c in ['observed_at','entity','entity_type','source','value','evidence_id'] if c in ledger_df.columns]
    return ledger_df[cols].sort_values('observed_at').to_dict('records')

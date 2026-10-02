"""Calibração de confiança: compara o score do Tropeiro com veredictos humanos de casos passados."""

def brier(pairs):
    """`pairs`: [(prob 0-1, real 0/1)]. Menor é melhor; 0.25 = equivalente a chutar 50%."""
    return sum((p-y)**2 for p,y in pairs)/len(pairs) if pairs else None

def reliability(pairs,bins=5):
    """Por faixa de score: quantos casos e qual a taxa real de acerto. Idealmente taxa ≈ centro da faixa."""
    rows=[]
    for i in range(bins):
        lo,hi=i/bins,(i+1)/bins
        sel=[y for p,y in pairs if lo<=p<hi or (i==bins-1 and p==1)]
        if sel: rows.append({'range':f'{lo:.1f}-{hi:.1f}','cases':len(sel),'observed_rate':round(sum(sel)/len(sel),3)})
    return rows

def calibration_report(pairs,bins=5):
    return {'cases':len(pairs),'brier':None if not pairs else round(brier(pairs),4),'reliability':reliability(pairs,bins)}

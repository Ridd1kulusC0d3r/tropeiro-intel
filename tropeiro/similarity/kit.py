"""Fingerprint de kit de phishing: mesmo conjunto de arquivos estáticos => provável mesmo kit."""
import hashlib

def file_hashes(files):
    """`files`: {caminho_relativo: bytes}. Retorna {caminho: sha256}."""
    return {p.strip('/').lower():hashlib.sha256(b).hexdigest() for p,b in files.items()}

def kit_fingerprint(files):
    """Fingerprint estável: independe da ordem e do domínio que hospeda o kit."""
    h=file_hashes(files)
    return hashlib.sha256('\n'.join(f'{p}:{d}' for p,d in sorted(h.items())).encode()).hexdigest()

def kit_similarity(a,b):
    """Jaccard sobre pares (caminho, hash). 1.0 = idêntico; ~0.7+ = mesmo kit com pequenas edições."""
    sa=set(file_hashes(a).items()); sb=set(file_hashes(b).items())
    return len(sa&sb)/len(sa|sb) if sa|sb else 0.0

def cluster_kits(sites,threshold=0.7):
    """`sites`: {dominio: {caminho: bytes}}. Agrupa domínios com kits semelhantes (union-find simples)."""
    names=list(sites); parent={n:n for n in names}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if kit_similarity(sites[a],sites[b])>=threshold: parent[find(a)]=find(b)
    groups={}
    for n in names: groups.setdefault(find(n),[]).append(n)
    return [sorted(g) for g in groups.values() if len(g)>1]

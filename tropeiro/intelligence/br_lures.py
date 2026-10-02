"""Iscas brasileiras: marca/tema por regras editáveis + infraestrutura de pagamento/contato no texto."""
import json, re
from ..utils import extract_iocs, refang

# (marca, tema, palavras-chave em minúsculas). Edite aqui ou passe `rules=` / load_rules('arquivo.json').
RULES=[
    ('Receita Federal','regularização CPF',['receita federal','cpf irregular','regularize seu cpf','regularizar cpf']),
    ('Correios','taxa de encomenda',['correios','taxa de importação','encomenda retida','rastreio']),
    ('PIX/Banco Central','chave PIX / estorno',['chave pix','estorno pix','pix bloqueado','devolução pix']),
    ('Detran/CNH','multa / CNH',['detran','cnh suspensa','multa pendente','renavam']),
    ('Banco','conta bloqueada',['sua conta foi bloqueada','validação de conta','atualize seus dados','token expirado']),
    ('INSS/Gov.br','benefício',['inss','gov.br','benefício bloqueado','prova de vida']),
]

def load_rules(path):
    """JSON: [["Marca","tema",["kw1","kw2"]], ...]"""
    return [(m,t,[k.lower() for k in kws]) for m,t,kws in json.load(open(path,encoding='utf-8'))]

def detect_br_lures(text,rules=None):
    low=(text or '').lower(); out=[]
    for brand,theme,kws in rules or RULES:
        hit=[k for k in kws if k in low]
        if hit: out.append({'brand':brand,'theme':theme,'matched':hit})
    return out

def _digits_ok(d,weights):
    s=sum(int(x)*w for x,w in zip(d,weights)); r=(s*10)%11
    return r%10

def valid_cpf(v):
    d=re.sub(r'\D','',v)
    if len(d)!=11 or len(set(d))==1: return False
    return _digits_ok(d[:9],range(10,1,-1))==int(d[9]) and _digits_ok(d[:10],range(11,1,-1))==int(d[10])

def valid_cnpj(v):
    d=re.sub(r'\D','',v)
    if len(d)!=14 or len(set(d))==1: return False
    def dv(n,w): r=sum(int(x)*k for x,k in zip(n,w))%11; return 0 if r<2 else 11-r
    w1=[5,4,3,2,9,8,7,6,5,4,3,2]; w2=[6]+w1
    return dv(d[:12],w1)==int(d[12]) and dv(d[:13],w2)==int(d[13])

RE_CPF=re.compile(r'(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)')
RE_CNPJ=re.compile(r'(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)')
RE_EVP=re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',re.I)
RE_PIX_COPIA=re.compile(r'\b000201[0-9A-Za-z .\-@/:]{40,}6304[0-9A-F]{4}\b')
RE_WA=re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=)\+?(\d{10,15})',re.I)

def extract_lure_infra(text):
    """IOCs padrão + CPF/CNPJ (só com dígito verificador válido), chave PIX aleatória, PIX copia-e-cola e WhatsApp."""
    text=refang(text); out=extract_iocs(text)
    cpf=sorted({re.sub(r'\D','',x) for x in RE_CPF.findall(text) if valid_cpf(x)})
    cnpj=sorted({re.sub(r'\D','',x) for x in RE_CNPJ.findall(text) if valid_cnpj(x)})
    if cpf: out['cpf']=cpf
    if cnpj: out['cnpj']=cnpj
    evp=sorted({x.lower() for x in RE_EVP.findall(text)})
    if evp: out['pix_evp']=evp
    br=sorted(set(RE_PIX_COPIA.findall(text)))
    if br: out['pix_copia_cola']=br
    wa=sorted(set(RE_WA.findall(text)))
    if wa: out['whatsapp']=wa
    return out

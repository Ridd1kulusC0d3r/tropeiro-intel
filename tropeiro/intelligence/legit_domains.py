"""Plataformas legítimas que aparecem em iscas. Servem de contexto, nunca de bloqueio por domínio."""
from ..utils import hostname

MESSAGING={'wa.me','whatsapp.com','t.me','telegram.org'}
KNOWN_LEGIT={*MESSAGING,'facebook.com','instagram.com','google.com','youtube.com','linkedin.com',
             'microsoft.com','apple.com','twitter.com','x.com','gov.br'}

def is_known_legit(value):
    h=hostname(str(value))
    return any(h==s or h.endswith('.'+s) for s in KNOWN_LEGIT)

def _messaging(value):
    h=hostname(str(value)); return any(h==s or h.endswith('.'+s) for s in MESSAGING)

def partition_iocs(iocs):
    """Separa IOCs em (acionáveis, só_contexto).

    - domínio em plataforma legítima: contexto (bloquear `google.com` ou `wa.me` quebraria usuários);
    - URL em app de mensagem: contexto (o IOC real é o número, já extraído como `whatsapp`/`phone`);
    - URL em outra plataforma legítima (ex.: um formulário hospedado): continua acionável por URL.
    """
    act,ctx={},{}
    for typ,vals in iocs.items():
        for v in vals:
            legit=typ=='domain' and is_known_legit(v) or typ=='url' and _messaging(v)
            (ctx if legit else act).setdefault(typ,[]).append(v)
    return act,ctx

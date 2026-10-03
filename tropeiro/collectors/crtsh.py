import time, urllib.error
from ..http import get
from ..utils import valid_hostname

TRANSIENT = {404, 429, 500, 502, 503, 504}     # o crt.sh devolve 404/502/503 de forma intermitente quando está sobrecarregado

def lookup(domain, attempts=2, pause=1.5):
    d = valid_hostname(domain)
    if not d:
        raise ValueError(f'hostname inválido: {domain!r}')
    last = None
    for i in range(attempts):
        try:
            return get(f'https://crt.sh/?q=%25.{d}&output=json', timeout=20, retries=0)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in TRANSIENT or i == attempts - 1:
                raise
            time.sleep(pause)
    raise last

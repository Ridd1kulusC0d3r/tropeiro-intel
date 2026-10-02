from ..http import get
from ..utils import valid_hostname

def lookup(domain):
    d=valid_hostname(domain)
    if not d: raise ValueError(f'hostname inválido: {domain!r}')
    return get(f'https://crt.sh/?q=%25.{d}&output=json',timeout=60)

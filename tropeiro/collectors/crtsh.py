from ..http import get

def lookup(domain): return get(f'https://crt.sh/?q=%25.{domain}&output=json',timeout=60)

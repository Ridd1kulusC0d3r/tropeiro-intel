"""Testes são offline: qualquer chamada real de rede via urllib falha de forma explícita."""
import urllib.request
import pytest

@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def blocked(*a,**k): raise RuntimeError('rede bloqueada nos testes (use monkeypatch)')
    monkeypatch.setattr(urllib.request,'urlopen',blocked)

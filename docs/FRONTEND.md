# Investigation Workbench

Front em **Gradio** (Python puro, roda no Colab ou local).

```python
from tropeiro.frontend.app import build_app
build_app().launch()
```

Abas: **Grafo** · **IOCs** (decisão BLOCK/HUNT/MONITOR) · **Isca e IA** · **Dados** (relações, ledger, saúde das fontes) · **Linha do tempo** · **Memória** · **Exportar** (STIX, MISP, Sigma, relatório, ZIP).

- O botão **Carregar caso de demonstração** funciona sem rede (`tropeiro.frontend.demo`).
- `tropeiro.frontend.views` contém renderizadores HTML/SVG puros (escapam todo texto externo) e podem ser reutilizados em relatórios.
- O grafo é SVG gerado com NetworkX, sem dependência de JavaScript externo. Linha contínua = evidência; tracejada = ligação proposta pela IA.

## Regenerar GIF e capturas

```bash
pip install playwright pillow gradio
python scripts/make_demo_media.py     # CHROME_PATH=/caminho/chrome se o Playwright não achar o navegador
```

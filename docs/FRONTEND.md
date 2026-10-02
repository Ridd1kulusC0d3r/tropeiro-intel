> **Manual de uso completo:** [USER_GUIDE.md](USER_GUIDE.md). Esta página descreve só a estrutura do front.

# Investigation Workbench

Front em **Gradio** (Python puro, roda no Colab ou local).

```bash
tropeiro workbench
```

Pelo Python: `launch_local()` (computador) ou `launch_colab_frontend()` (Colab) em `tropeiro.frontend.app`. Use-as em vez de `build_app().launch()`: no Gradio 6 o tema é aplicado no `launch()`, e estas funções cuidam disso.

Abas: **Grafo** · **IOCs** (decisão BLOCK/HUNT/MONITOR) · **Isca e IA** · **Dados** (relações, ledger, saúde das fontes) · **Linha do tempo** · **Memória** · **Exportar** (STIX, MISP, Sigma, relatório, ZIP).

- O botão **Carregar caso de demonstração** funciona sem rede (`tropeiro.frontend.demo`).
- `tropeiro.frontend.views` contém renderizadores HTML/SVG puros (escapam todo texto externo) e podem ser reutilizados em relatórios.
- O grafo é SVG gerado com NetworkX, sem dependência de JavaScript externo. Linha contínua = evidência; tracejada = ligação proposta pela IA.

## Regenerar GIF e capturas

```bash
pip install playwright pillow gradio
python scripts/make_demo_media.py     # CHROME_PATH=/caminho/chrome se o Playwright não achar o navegador
```

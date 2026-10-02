# Instalação

O Tropeiro roda de três formas. A primeira exige só um navegador.

| Forma | Quando usar | Requisitos |
|---|---|---|
| **Google Colab** | primeiro contato, sem instalar nada | conta Google |
| **Local (pip)** | uso diário, Workbench no navegador, CLI offline, integração em scripts | Python 3.10 a 3.13 |
| **Desenvolvimento** | contribuir ou alterar o código | Python + git |

## 1. Google Colab

Abra o [notebook oficial](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb) e execute a célula **01 · Bootstrap**. Ela clona o repositório, instala as dependências e confirma a versão. Detalhes em [COLAB.md](COLAB.md).

O disco do Colab é temporário. Para guardar a [Campaign Memory](CAMPAIGN_MEMORY.md) entre sessões, monte o Google Drive e aponte a memória para `/content/drive/MyDrive/...` (veja [CONFIGURATION](CONFIGURATION.md#campaign-memory)).

## 2. Local

```bash
git clone https://github.com/Ridd1kulusC0d3r/tropeiro-intel.git
cd tropeiro-intel
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[colab]"          # núcleo + Workbench (Gradio) + dnstwist
```

### Extras

| Extra | Instala | Use para |
|---|---|---|
| *(nenhum)* | `tldextract`, `rapidfuzz`, `pandas`, `networkx`, `stix2` | CLI, bibliotecas, exportações |
| `colab` | `dnstwist`, `ipywidgets`, `gradio` | Workbench e geração de lookalikes |
| `colab-full` | `dnstwist[full]` e o resto de `colab` | recursos extras do dnstwist (ex.: whois, GeoIP, hashes fuzzy) |
| `ai` | `gliner`, `transformers`, `accelerate`, `sentencepiece`, `protobuf` | extração com GLiNER e análise com Qwen |
| `dev` | `pytest`, `ruff` | rodar os testes e o lint |

Combine com vírgula: `pip install -e ".[colab,ai]"`.

### Verifique

```bash
python -c "import tropeiro; print(tropeiro.__version__)"
tropeiro --help
tropeiro lure examples/lure_receita.txt          # deve listar a marca Receita Federal e o domínio receita-regulariza.example
tropeiro workbench                               # abre http://127.0.0.1:7860 ; use o botão "Carregar caso de demonstração"
```

Se o comando `tropeiro` não for encontrado, o ambiente virtual não está ativo; use `python -m tropeiro.cli ...`.

## 3. IA (opcional)

O Tropeiro **funciona sem modelos**: as regras brasileiras sempre rodam. Os modelos acrescentam entidades de contexto e uma análise textual.

| Modelo | Tamanho aproximado | Hardware |
|---|---|---|
| GLiNER `urchade/gliner_multi-v2.1` | ~1 GB | CPU funciona |
| Qwen3 0,6B (padrão em CPU) | ~1,5 GB | CPU funciona, lento |
| Qwen3 1,7B (padrão com GPU) | ~3,5 GB | GPU recomendada |

Os modelos são baixados do Hugging Face na primeira execução. `runtime_profile()` escolhe o Qwen conforme haja GPU. Nada é enviado a APIs externas: a inferência é local.

> Validado de verdade em CPU com a isca de exemplo (veja [AI](AI.md#validação-com-modelos-reais)). Ainda não foi medido em GPU nem em casos reais.

## 4. Desenvolvimento

```bash
pip install -e ".[dev,colab]"
pytest -q                                       # testes (offline)
ruff check --select E9,F63,F7,F82 .             # lint usado na CI
python scripts/make_demo_media.py               # regenera capturas e GIF (precisa de playwright e pillow)
```

## Atualizando

```bash
git pull && pip install -e ".[colab]"
```

Faça cópia do arquivo da [Campaign Memory](CAMPAIGN_MEMORY.md) antes de atualizar; ele é o único estado persistente do projeto.

## Problemas na instalação

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: gradio` | instalou sem o extra | `pip install -e ".[colab]"` |
| `tropeiro: command not found` | venv inativo ou instalação sem `-e` | ative o venv ou use `python -m tropeiro.cli` |
| Workbench abre sem tema escuro | Gradio antigo/incompatível | `pip install -U "gradio>=4.44,<7"` |
| `torch` enorme no `pip install .[ai]` | dependência do `transformers` | use um ambiente separado para IA |
| `SentencePieceExtractor requires the protobuf library` ou `tiktoken is required` ao carregar o GLiNER | faltavam `sentencepiece` e `protobuf` (extra `ai` antes da 4.7) | `pip install sentencepiece protobuf` ou reinstale com `.[ai]` |

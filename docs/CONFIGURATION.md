# Configuração

Tudo tem padrão seguro: **PASSIVE**, profundidade **balanced**, sem sondagem HTTP, sem chaves de API.

## Modos de operação

| Modo | O que muda | Quando usar |
|---|---|---|
| `PASSIVE` | só fontes públicas e passivas | **quase sempre** |
| `SAFE_ENRICHMENT` | liga também o Common Crawl | quando quiser mais histórico, ainda sem tocar no alvo |
| `AUTHORIZED_ACTIVE` | permite sondagem direta, **só** com `enable_http_probe=True` | exclusivamente para ativos seus ou com autorização por escrito |

Escolher `AUTHORIZED_ACTIVE` sozinho não liga a sondagem: `Settings.active_allowed()` exige o modo **e** o `enable_http_probe`.

## Profundidade (`provider_budget`)

| Valor | `DNSTWIST_MAX` (lookalikes) | `URLSCAN_DETAIL_MAX` (detalhes de scans) | FOFA / Censys |
|---|---|---|---|
| `free` | 80 | 5 | **desligados** mesmo com chave |
| `balanced` (padrão) | 250 | 12 | ligados se houver chave |
| `extended` | 600 | 30 | ligados se houver chave |

Com **mais de 10 alvos** os limites caem proporcionalmente (mínimos: 25 lookalikes e 2 detalhes), para o lote não estourar as fontes. Fontes fora da profundidade aparecem como `SKIPPED_BUDGET`; sem chave, `SKIPPED_MISSING_SECRET`. Nenhum dos dois é erro.

## O que liga em cada superfície

| Recurso | Notebook Colab | Workbench e `tropeiro search` | CLI `lure` |
|---|---|---|---|
| DNS, RDAP, crt.sh (domínio, URL, e-mail, lote, isca) | sim | sim | não (offline) |
| Wayback (histórico) | sim | sim | não |
| Common Crawl | só em `SAFE_ENRICHMENT` | só em `SAFE_ENRICHMENT` | não |
| urlscan (busca) e OTX | sim | sim | não |
| urlscan: detalhes e **identificadores duráveis** (GA, GTM, AdSense, pixel) | sim | sim, até `URLSCAN_DETAIL_MAX` scans | não |
| **IP**: DNS reverso (PTR), RDAP da rede, scans do urlscan que viram o IP | não | **sim** | não |
| VirusTotal, ThreatFox (domínio, IP e **hash**) | com chave | com chave | não |
| dnstwist e similaridade de domínios | sim | não | não |
| DNSDumpster, FOFA, Censys | com chave | não | não |
| **Lotes de registro** (criados em sequência, mesmo registrar/NS) | não | sim, com 2+ domínios | não |
| **Iscas parecidas** em casos anteriores | não | sim, com Campaign Memory | não |
| Extração de entidades da isca | GLiNER opcional (AI-01) + célula **08B** (regras BR) | **regras BR + GLiNER opcional** | **regras BR** (sem modelo) |
| Exportações | Export Center (ZIP seletivo) + célula **55B** (STIX 2.1, MISP, Sigma) | **STIX 2.1, MISP e Sigma** no ZIP | **STIX 2.1, MISP e Sigma** |

O Workbench e o `tropeiro search` usam **o mesmo pipeline**; a tabela de fontes por tipo de alvo está em [SEARCH_TYPES](SEARCH_TYPES.md).

**Modo e profundidade valem no notebook, no Workbench e na CLI.** O Workbench ainda não roda dnstwist, DNSDumpster, FOFA e Censys: para a investigação mais ampla use o notebook.

No Workbench, `free` / `balanced` / `extended` mudam quantos scans do urlscan têm o detalhe baixado (5 / 12 / 30). Sem chaves, VirusTotal e ThreatFox aparecem como `SKIPPED_MISSING_SECRET` na saúde das fontes.

> **Privacidade da memória.** Com a Campaign Memory ligada, o Workbench guarda o **texto da isca** no banco local (`lure_texts`) para comparar iscas entre casos. Esse texto **não** vai para `case.json`, relatório nem ZIP exportados. Se a mensagem tiver dados de vítimas, desmarque "Usar Campaign Memory" ou apague o arquivo `.sqlite`.

## Chaves de API (todas opcionais)

Defina como **Colab Secrets** (ícone de chave no Colab) ou como **variáveis de ambiente**. O nome precisa ser exatamente este:

| Variável | Fonte | Sem a chave |
|---|---|---|
| `URLSCAN_API_KEY` | urlscan.io | funciona com limites públicos mais baixos |
| `VT_API_KEY` | VirusTotal | a fonte é pulada (`SKIPPED_MISSING_SECRET`) |
| `THREATFOX_AUTH_KEY` | ThreatFox (abuse.ch) | a fonte é pulada |
| `DNSDUMPSTER_API_KEY` | DNSDumpster | a fonte é pulada |
| `FOFA_API_KEY` | FOFA | a fonte é pulada |
| `CENSYS_PAT` e `CENSYS_ORG_ID` | Censys | a fonte é pulada |

```bash
export URLSCAN_API_KEY="..."        # Linux/macOS
$env:URLSCAN_API_KEY="..."          # PowerShell
```

Um modelo está em [`.env.example`](../.env.example). **Nunca** faça commit de chaves.

### Fontes sem chave (núcleo)

| Fonte | Para quê |
|---|---|
| Cloudflare DNS-over-HTTPS | resolução A, AAAA, CNAME, MX, NS |
| rdap.org | registro do domínio (datas, registrar, nameservers) |
| crt.sh | nomes em certificados (Certificate Transparency) |
| Wayback Machine, Common Crawl | histórico de URLs |
| urlscan.io (busca pública), OTX | scans e URLs já observados |
| PhishTank | consulta de URL (chave de app opcional) |

## Prazo, tempo limite e estados das consultas

A coleta roda **em paralelo** (uma tarefa por fonte e assunto) e **nenhuma fonte lenta trava a busca**:

| Ajuste | Padrão | Onde |
|---|---|---|
| Prazo total da coleta | 45 s / 90 s / 180 s (`free` / `balanced` / `extended`) | `--deadline S` na CLI, parâmetro `deadline` de `investigate` |
| Tempo limite de cada chamada | 20 s | `http.TIMEOUT_CAP` |
| Tentativas | 2 novas tentativas **só** em 429/500/502/503/504 e falhas de rede; 404 e 400 não repetem | argumento `retries` |
| Wayback e Common Crawl | **1 tentativa** (fontes instáveis; o prazo decide) | `collectors/history.py` |
| crt.sh | 2 tentativas, **inclusive em 404/502/503** (resposta intermitente quando sobrecarregado) | `collectors/crtsh.py` |
| `Retry-After` | respeitado, até 30 s | automático |
| Intervalo mínimo por host | 0,3 s; **1,0 s** em urlscan.io, crt.sh, web.archive.org e index.commoncrawl.org | `http.MIN_INTERVAL`, `http.HOST_INTERVALS` |
| Detalhes do urlscan | **2 falhas seguidas e para** (evita 12 erros 403 em fila) | automático |
| Cache de GET em disco | **ligado no Workbench e na CLI** (1 h); desligado na API de baixo nível | `--no-cache`, `http.set_cache(...)` |

Cada consulta termina em um destes **estados** (aparecem em *Dados → Saúde das fontes* e na CLI):

| Estado | Significa |
|---|---|
| `OK` | respondeu |
| `UNAVAILABLE` | tentou e falhou; a coluna *observação* diz por quê (ex.: `HTTP 403 — acesso negado (a fonte pode exigir chave de API)`, `falha de rede (...)`) |
| `TIMEOUT` | não terminou dentro do prazo total; o resultado sai **parcial** |
| `SKIPPED_MISSING_SECRET` | falta a chave (opcional); a mensagem diz qual variável definir |
| `SKIPPED_MODE` | só roda em outro modo (Common Crawl: `SAFE_ENRICHMENT`) |
| `NOT_NEEDED` | o alvo não tem o que consultar (telefone, hash sem chave, texto sem domínio/IP) e a mensagem explica |

```python no-run
from tropeiro import http
http.MIN_INTERVAL = 0.5                           # mais gentil com as fontes
http.HOST_INTERVALS["otx.alienvault.com"] = 2.0   # intervalo próprio para um host
http.set_cache("~/.tropeiro/cache", ttl=6*3600)   # repetir a mesma consulta não chama a fonte de novo
```

O cache só vale para GET sem cabeçalhos próprios (requisições com chave não são cacheadas, para não gravar respostas autenticadas em disco).

## Validação do alvo

Domínios e hostnames passam por `valid_hostname` antes de entrar numa URL de coletor (crt.sh, RDAP). Valores com `/`, `?`, `&`, espaço ou sem TLD são rejeitados com `ValueError`. Domínios internacionais são convertidos para punycode (`bücher.de` → `xn--bcher-kva.de`).

## Campaign Memory

| Onde | Caminho padrão |
|---|---|
| Colab | `/content/tropeiro_case_memory.sqlite` (some ao apagar o runtime) |
| Local | `~/.tropeiro/tropeiro_case_memory.sqlite` |

Para mudar: variável `TROPEIRO_MEMORY_PATH`, o campo "Arquivo da memória" nas opções avançadas do Workbench, ou `CaseMemory("/outro/caminho.sqlite")`. No Colab, para persistir:

```python no-run
from google.colab import drive; drive.mount("/content/drive")
# memória em: /content/drive/MyDrive/tropeiro_case_memory.sqlite
```

## Diretório de trabalho

Cada caso é gravado em `<base>/tropeiro_ui_<ID_DO_CASO>/` com `report/` e `export/`. A base é, nesta ordem: a variável **`TROPEIRO_WORKSPACE`**, `/content` (Colab) ou o diretório temporário do sistema. Na CLI, `--workspace DIR` escolhe a pasta do caso. O Workbench publica cópias dos arquivos numa pasta que o Gradio aceita servir e libera a pasta-base com `allowed_paths`.

## Campos de `Settings`

`tropeiro.config.Settings` reúne os parâmetros do pipeline:

| Campo | Padrão | Significado |
|---|---|---|
| `case_id` | `TI-001` | identificador do caso (vira nome de pasta) |
| `analyst` | `Analista` | quem conduz |
| `brand` | `""` | marca imitada (melhora o contexto de lookalikes) |
| `mode` | `PASSIVE` | veja acima |
| `provider_budget` | `balanced` | veja acima |
| `max_workers` | `8` | reservado para coleta em paralelo (ainda não usado pelo Workbench) |
| `cache_ttl_seconds` | `3600` | TTL de cache (para o cache HTTP use `http.set_cache(..., ttl=...)`) |
| `enable_http_probe` | `False` | sondagem direta (exige `AUTHORIZED_ACTIVE`) |
| `source_reliability` | por fonte | peso de cada fonte no Evidence Ledger (DNS e RDAP 0,95; crt.sh 0,90; OTX 0,70 ...) |

## Política de decisão

Os limiares de BLOCK/HUNT/MONITOR são a `DEFAULT_POLICY` em `tropeiro/intelligence/decision_objects.py` e podem ser sobrescritos passando `policy={...}` a `build_ioc_decisions`. Veja [INTERPRETING_RESULTS](INTERPRETING_RESULTS.md#decisão-por-ioc).

## Regras de iscas brasileiras

As marcas/temas são a lista `RULES` em `tropeiro/intelligence/br_lures.py`. Para usar as suas, sem editar o código:

```python
import json, tempfile
from pathlib import Path
from tropeiro.intelligence.br_lures import load_rules, detect_br_lures

with tempfile.TemporaryDirectory() as pasta:
    arquivo = Path(pasta) / "minhas_regras.json"      # formato: [["Marca", "tema", ["palavra 1", "palavra 2"]], ...]
    arquivo.write_text(json.dumps([["Banco Aurora", "conta bloqueada", ["conta aurora bloqueada"]]]), encoding="utf-8")
    regras = load_rules(arquivo)
    assert detect_br_lures("Atenção: sua conta Aurora bloqueada!", regras)[0]["brand"] == "Banco Aurora"
```

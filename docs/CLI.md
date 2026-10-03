# Linha de comando

A CLI roda **sem interface**. `search` faz a busca completa (coleta nas fontes públicas); `doctor` diagnostica o ambiente; `lure` analisa o texto de uma isca **100% offline**; `workbench` abre a interface.

```text
tropeiro search ALVO [--type T] [--mode M] [--budget B] [--case ID] [--ai A] [--out/--workspace DIR] [--deadline S] [--json] [-q]
tropeiro doctor [--offline]
tropeiro lure ARQUIVO [--case ID] [--tlp COR] [--out DIR]
tropeiro workbench [--port N] [--share] [--no-browser]
```

Sem instalar o comando: `python -m tropeiro.cli ...`.

## `tropeiro search`: busca completa sem interface

É a mesma investigação do Workbench (mesmo pipeline), com o progresso no terminal. Use para testar o ambiente, automatizar ou rodar em servidor.

```bash
tropeiro search example.com
```

```text
Tropeiro Intel 4.8.0 · caso TI-CLI-001
Alvo: example.com  [DOMAIN]  modo PASSIVE · profundidade balanced · prazo 90s
Assuntos: 1 domínio(s), 0 IP(s), 0 hash(es) → 10 consultas em paralelo
  ✓ dns:A              example.com                    0.4s  2 itens
  ✓ rdap               example.com                    0.6s  3 itens
  ✓ otx                example.com                    0.2s  200 itens
  ✓ dns:AAAA           example.com                    0.7s  2 itens
  ✓ dns:CNAME          example.com                    0.8s
  ✓ dns:MX             example.com                    1.0s  1 itens
  ✓ dns:NS             example.com                    1.3s  2 itens
  ✓ urlscan            example.com                    3.1s  100 itens
  ✗ wayback            example.com                   12.9s — falha de rede ([Errno 104] Connection reset by peer)
  ✗ crt.sh             example.com                   15.0s — HTTP 502
  – commoncrawl        SKIPPED_MODE: só no modo SAFE_ENRICHMENT
  – virustotal         SKIPPED_MISSING_SECRET: defina VT_API_KEY para ativar (opcional)
  – threatfox          SKIPPED_MISSING_SECRET: defina THREATFOX_AUTH_KEY para ativar (opcional)

Concluído em 15.1s · 311 evidências · 8 fontes OK · 3 indisponíveis · 3 puladas
IOC                                          tipo     decisão              confiança     risco FP
example.com                                  domain   HUNT                 LOW           MEDIUM
Relatório: <pasta de trabalho>/report/Tropeiro_Intel_Report.html
Pacote:    <pasta de trabalho>/Tropeiro_TI-CLI-001_Package.zip
```

(saída **real** de uma execução; os tempos e quais fontes falham variam com a sua rede. Aqui o Wayback e, às vezes, o crt.sh estavam instáveis: a busca seguiu e entregou o resultado sem eles.)

| Argumento | Padrão | Significado |
|---|---|---|
| `ALVO` | obrigatório | domínio, URL, IP, e-mail, hash, telefone, **texto da isca**, caminho de um arquivo de texto ou `-` (entrada padrão) |
| `--type` | `AUTO` | força o tipo (`DOMAIN`, `URL`, `IP`, `EMAIL`, `HASH`, `PHONE`, `MULTI_IOC`, `LURE_TEXT`) |
| `--mode` | `PASSIVE` | `PASSIVE`, `SAFE_ENRICHMENT` (liga Common Crawl) ou `AUTHORIZED_ACTIVE` |
| `--budget` | `balanced` | `free`, `balanced`, `extended`: limites e prazo (45 / 90 / 180 s) |
| `--deadline S` | conforme o `--budget` | prazo total da coleta; o que não terminar vira `TIMEOUT` e o resultado sai parcial |
| `--case`, `--analyst`, `--brand` | `TI-CLI-001`, `Analista`, vazio | metadados do caso |
| `--ai` | `OFF` | `GLINER_ONLY`, `GLINER_QWEN` ou `AUTO` |
| `--no-memory`, `--memory-path` | memória ligada | Campaign Memory |
| `--workspace DIR` | pasta de trabalho padrão | onde gravar relatório, exportações e ZIP |
| `--no-cache` | cache ligado (1 h) | ignora o cache de respostas |
| `--json` | texto | imprime o resumo, as decisões e as fontes em JSON |
| `-q` | | silencia o progresso (só o resultado) |

**Códigos de saída:** `0` concluiu; `2` **nenhuma fonte respondeu** (quase sempre rede/proxy: rode `tropeiro doctor`); `1` erro (a mensagem diz qual).

O que cada tipo de alvo consulta: [SEARCH_TYPES](SEARCH_TYPES.md).

## `tropeiro doctor`: diagnóstico

```bash
tropeiro doctor            # inclui o teste de rede até cada fonte
tropeiro doctor --offline  # só Python, dependências e pastas
```

```text
Tropeiro Intel 4.8.0 · diagnóstico
✓ Python                                     3.11.15 (Linux)
✓ dependência: tldextract                    5.3.2
✓ dependência: rapidfuzz                     3.14.6
✓ dependência: pandas                        2.3.3
✓ dependência: networkx                      3.6.1
✓ dependência: stix2                         3.0.2
✓ Workbench (gradio)                         5.50.0
✓ IA opcional (GLiNER/Qwen)                  completa
✓ pasta de trabalho                          /tmp
✓ pasta ~/.tropeiro (cache e memória)        /home/voce/.tropeiro
✓ proxy                                      HTTPS_PROXY, https_proxy
✓ chaves de API (opcionais)                  nenhuma (o núcleo funciona sem)
✓ rede: DNS-over-HTTPS (cloudflare-dns.com)  HTTP 200 em 0.3s
✓ rede: RDAP (rdap.org)                      HTTP 200 em 0.6s
⚠ rede: crt.sh                               HTTP 502 em 0.9s
    → a fonte respondeu mas recusou (pode exigir chave ou ter limite de uso)
✓ rede: urlscan.io                           HTTP 200 em 0.8s
⚠ rede: Wayback Machine                      URLError: <urlopen error [Errno 104] Connection reset by peer>
    → fonte opcional inalcançável: a busca segue sem ela (status UNAVAILABLE)
✓ rede: AlienVault OTX                       HTTP 200 em 2.2s
Resultado: DEGRADADO
```

`OK` (tudo certo), `DEGRADADO` (algo **opcional** falhou: a busca funciona) ou `FALHA` (algo essencial falhou: DNS-over-HTTPS, RDAP, uma dependência ou uma pasta; sai com código `1`).

## `tropeiro lure`: analisar o texto de uma isca (offline)

Lê uma mensagem (arquivo, ou `-` para a entrada padrão), identifica marca/tema, extrai IOCs e, com `--out`, exporta STIX 2.1, MISP e Sigma.

| Opção | Padrão | Significado |
|---|---|---|
| `ARQUIVO` | obrigatório | texto da isca; `-` lê da entrada padrão |
| `--case ID` | `CASE` | identificador do caso (entra nos IDs dos arquivos exportados) |
| `--tlp COR` | `AMBER` | `WHITE`/`CLEAR`, `GREEN`, `AMBER` ou `RED` (marcação TLP) |
| `--out DIR` | *(não exporta)* | pasta de saída; é criada se não existir |

O texto é "refangado" antes da análise: `hxxps://x[.]com` é lido como `https://x.com`.

### Exemplo

```bash
tropeiro lure examples/lure_receita.txt --case CASO-001 --tlp AMBER --out saida/
```

Entrada (`examples/lure_receita.txt`):

```text
Receita Federal: seu CPF está irregular. Regularize hoje em hxxps://receita-regulariza[.]example/cpf ou fale com o atendimento https://wa.me/5511999990000. Não perca o prazo. Banco Aurora S.A.
```

Saída:

```json
{
  "lures": [
    {"brand": "Receita Federal", "theme": "regularização CPF", "matched": ["receita federal"]}
  ],
  "iocs": {
    "url": ["https://receita-regulariza.example/cpf", "https://wa.me/5511999990000"],
    "phone": ["5511999990000"],
    "domain": ["receita-regulariza.example", "wa.me"],
    "whatsapp": ["5511999990000"]
  },
  "somente_contexto": {
    "url": ["https://wa.me/5511999990000"],
    "domain": ["wa.me"]
  }
}
defanged: receita-regulariza[.]example
exportado em saida/
```

Leitura:

- `lures`: a marca/tema reconhecido. Lista vazia = nenhuma regra conhecida bateu (não significa que seja legítima).
- `iocs`: tudo que foi extraído.
- `somente_contexto`: IOCs em **plataformas legítimas** (aqui, WhatsApp). Ficam no relatório mas **não** viram regra de bloqueio: bloquear `wa.me` quebraria o WhatsApp para todos. O número de telefone, esse sim, é o IOC.
- `defanged`: os domínios acionáveis já defangados, prontos para colar em um relatório ou e-mail.

### Arquivos gerados em `--out`

| Arquivo | Conteúdo |
|---|---|
| `stix.json` | pacote STIX 2.1 com `Campaign`, `Indicator`, observáveis e relações |
| `misp.json` | evento MISP com tags `tlp:*` e `type:phishing` |
| `sigma_dns.yml` | regra Sigma de consulta DNS (só se houver domínio acionável) |
| `sigma_network.yml` | regra Sigma de conexão a IP (só se houver IP) |

Detalhes de cada formato: [OUTPUTS](OUTPUTS.md).

### Pela entrada padrão

```bash
pbpaste | tropeiro lure - --case C2          # macOS
xclip -o | tropeiro lure - --case C2         # Linux
```

### Em scripts e CI

A CLI termina com código `0` quando conclui; erro de uso (opção inválida) e arquivo inexistente terminam com código diferente de zero. Para usar a saída JSON em outra ferramenta, a primeira parte (até a linha `defanged:`) é JSON; para uso programático prefira a [API Python](PYTHON_API.md), que devolve estruturas diretamente.

## `tropeiro workbench`

Abre o [Workbench](USER_GUIDE.md) no navegador local e bloqueia até `Ctrl+C`.

| Opção | Padrão | Significado |
|---|---|---|
| `--port N` | primeira livre ≥ 7860 | porta local |
| `--share` | desligado | cria link público temporário do Gradio. **Não use com dados de casos reais** |
| `--no-browser` | abre o navegador | não abre o navegador (servidores, SSH) |

Sem `--port`, usa a **primeira porta livre** a partir de 7860 e imprime a URL. Escuta apenas em `127.0.0.1`.

## Limitações da CLI

- `lure` não coleta nada da rede; para coletar use `tropeiro search`, o Workbench ou o notebook.
- Usa só regras; para entidades de contexto (organização, registrar) com GLiNER use a [API Python](PYTHON_API.md#extração-híbrida) ou o Workbench.
- Regras de marca: lista curta e editável ([CONFIGURATION](CONFIGURATION.md#regras-de-iscas-brasileiras)).

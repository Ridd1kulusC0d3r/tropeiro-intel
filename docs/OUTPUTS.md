# Saídas e formatos

O que o Tropeiro entrega, arquivo por arquivo, e como levar para outras ferramentas.

## Visão geral

| Superfície | O que gera |
|---|---|
| Workbench | pasta `export/` com `report.html`, `case.json`, `evidence_ledger.csv`, `ioc_decisions.csv`, `stix.json`, `misp.json`, `sigma_*.yml`, `manifest.json`, e o ZIP `Tropeiro_<caso>_Package.zip` com tudo isso |
| Notebook (Export Center) | seleção entre ~20 arquivos: relatório, CSVs de cada análise, JSONs de grafo/fingerprints, STIX e MISP do caso |
| CLI | `stix.json`, `misp.json`, `sigma_dns.yml`, `sigma_network.yml` |

## Integridade: `manifest.json`

Lista cada arquivo com tamanho e SHA-256. Use para provar que o pacote não foi alterado:

```json
[
  {"file": "case.json", "sha256": "…", "bytes": 48213},
  {"file": "stix.json", "sha256": "…", "bytes": 10734}
]
```

```bash
sha256sum case.json stix.json        # compare com o manifest
```

## `report.html`

Relatório único, **offline** (sem CDN), com filtros, tema claro/escuro, impressão/PDF e exportação no navegador. Ordem: avaliação executiva, ações, decisões por IOC, campanha, atribuição, lacunas e pivôs, detecção, evidências, fontes. Um caso com módulos ausentes sai marcado como **relatório parcial**.

## `evidence_ledger.csv`

Uma linha por observação.

| Coluna | Significado |
|---|---|
| `evidence_id` | identificador determinístico (`ev-` + hash); o mesmo fato gera o mesmo id |
| `entity`, `entity_type` | a quem a observação se refere |
| `source` | de onde veio (`dns:A`, `rdap:registrar_org`, `crt.sh`, `urlscan`, `manual/input`...) |
| `value` | o valor observado |
| `observed_at` | quando foi observado (UTC, ISO 8601) |
| `confidence` | `observed` ou `derived` |
| `notes` | contexto livre da observação |
| `source_reliability` | peso da fonte (0 a 1) |
| `derived` | `True` se for inferência, nunca coleta direta |

Itens da IA **não** entram neste arquivo.

## `ioc_decisions.csv`

| Coluna | Significado |
|---|---|
| `ioc`, `ioc_type` | indicador e tipo |
| `decision` | `BLOCK`, `TAKEDOWN_CANDIDATE`, `HUNT`, `MONITOR`, `DO_NOT_BLOCK`, `INSUFFICIENT_EVIDENCE` |
| `confidence`, `confidence_band` | 0–1 e a banda |
| `actionability` | confiança menos penalidades de listas de aviso (resolvers públicos, CDN, hosts compartilhados) |
| `severity` | `low`/`medium`/`high` |
| `evidence_count`, `independent_sources` | sustentação |
| `false_positive_risk` | `LOW`/`MEDIUM`/`HIGH` |
| `block_recommended`, `hunt_recommended`, `takedown_candidate`, `monitor_recommended` | booleanos |
| `expiration_guidance` | quando revalidar |
| `warning_hits` | listas de aviso que pesaram |
| `rationale` | por quê |

Significado de cada decisão: [INTERPRETING_RESULTS](INTERPRETING_RESULTS.md#decisão-por-ioc).

## `case.json`

O caso completo: metadados, avaliação executiva, decisões, evidências, relações, lacunas, pivôs e (se rodou) `ai_entities`, `ai_analysis`, `ai_metadata` e `cross_case_intelligence`. É o arquivo que a [Campaign Memory](CAMPAIGN_MEMORY.md) importa (`CaseMemory.import_case_json`).

## `stix.json`: STIX 2.1

Pacote com:

| Objeto | Detalhe |
|---|---|
| `marking-definition` | TLP escolhido (`--tlp`; padrão AMBER) |
| `campaign` | uma por caso, com ID determinístico |
| `domain-name`, `url`, `ipv4-addr`, `email-addr` | observáveis |
| `indicator` | `pattern` STIX, `valid_from`/`valid_until` (90 dias por padrão), `labels: ["phishing"]`, `confidence` quando informada |
| `relationship` | `indicator based-on observable` e `indicator indicates campaign` |

Exemplo de padrão: `[domain-name:value = 'receita-regulariza.example']`.

- IDs são **determinísticos** (UUIDv5 do caso + valor): reexportar não duplica no seu TIP.
- IOCs em plataformas legítimas entram **só como observáveis**, sem `indicator`.
- Aspas e barras no valor são escapadas no padrão.

Valide com a própria biblioteca: `stix2.parse(texto, allow_custom=True)`.

## `misp.json`: evento MISP

Um evento (`distribution: 0`, `analysis: 1`) com tags `tlp:*` e `type:phishing`.

| Tipo MISP | Origem | `to_ids` |
|---|---|---|
| `domain`, `url`, `ip-dst` | IOCs acionáveis | **true** |
| `md5`/`sha1`/`sha256` | hash, pelo tamanho | **true** |
| `email-dst`, `phone-number` | contexto | **false** |
| qualquer IOC de plataforma legítima | `Contexto (plataforma legítima): não bloquear` | **false** |

A política é conservadora de propósito: só o que é seguro bloquear vai com `to_ids=true`.

## Sigma

- `sigma_dns.yml`: consultas DNS a cada domínio, **igualdade exata ou subdomínio** (`.dominio`). `sigma_network.yml`: conexões a IPs.
- `status: experimental`, `level: medium`, `tags: attack.initial_access, attack.t1566`, e um aviso de falso positivo.
- O `id` é determinístico; domínios inválidos são descartados.

Converta para o seu SIEM com [`sigma-cli`](https://github.com/SigmaHQ/sigma-cli) (`sigma convert -t splunk -p ... sigma_dns.yml`; Elastic, Wazuh e outros também). Ajuste o mapeamento de campos (`query`, `dst_ip`) ao seu pipeline.

## Importando em outras ferramentas

| Destino | Como |
|---|---|
| **MISP** | *Add Event* → importar do formato MISP JSON (`misp.json`) |
| **OpenCTI** | *Data → Import* com `stix.json` |
| **Splunk/Elastic/Wazuh/Sentinel** | `sigma convert` sobre os `.yml` |
| **Planilha / BI** | abra os `.csv` (UTF-8) |

> Estes caminhos de importação seguem os formatos padrão (MISP JSON, STIX 2.1, Sigma), mas **não foram testados contra uma instância real** de MISP ou OpenCTI neste repositório. Se algo falhar, abra uma issue com a mensagem de erro.

## Boas práticas

- Compartilhe com o TLP apropriado e **sem** dados de vítimas.
- Revalide IOCs antes de bloquear: veja `expiration_guidance`.
- Guarde o `manifest.json` junto do pacote enviado.

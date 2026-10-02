# Roadmap

Princípio: **qualidade das relações acima da quantidade de APIs**. Python simples, passivo por padrão, IA sempre verificada.

## Onde estamos (4.6)

Funciona e está testado: coleta passiva, Evidence Ledger, Campaign Memory, Workbench v2, extração híbrida (regras BR + GLiNER), STIX/MISP/Sigma, CLI offline, retry/limite por host.

Existe como módulo, **mas ainda não está ligado ao Workbench/pipeline**: `similarity.kit`, `correlation.registration`, `intelligence.calibration`, `ai.lure_similarity`, `timeline_summary` e o cache HTTP (`http.set_cache`).

Nunca executado com modelos reais fora dos testes: GLiNER e Qwen (rodar no Colab e registrar o resultado).

## Fase 0 · Fechar o que já existe (concluída na 4.7)

| Item | Estado |
|---|---|
| Rodar GLiNER + Qwen reais | **feito em CPU** com a isca de exemplo; resultado em [AI](AI.md#validação-com-modelos-reais). Falta rodar em GPU e em casos reais anonimizados |
| `registration_batches` no Workbench | **feito** (aba Campanha) |
| `lure_similarity` com a Campaign Memory | **feito** (aba Campanha) |
| Cache HTTP no Workbench | **feito** (1 h, em `~/.tropeiro/cache`) |
| Workbench respeita modo e profundidade | **feito** (Wayback, Common Crawl, VirusTotal, ThreatFox, detalhes do urlscan) |
| Notebook com regras BR e exports novos | **feito** (células 08B e 55B) |
| CI com Gradio 5 e 6 | **feito** (job `workbench`) |
| Unificar os stores | **feito**: `storage/case_store.py` era código morto e foi removido |
| `cluster_kits` no pipeline | **pendente**: exige baixar os arquivos do site (favicon, JS), próxima fase |
| Release, topics, social preview | manual no GitHub |

## Fase 1 · Confiança nos números (1 mês)

- **Calibração real:** rotular 20–30 casos (campanha confirmada / coincidência) e publicar Brier + tabela de confiabilidade no README. É o diferencial mais raro: dizer quanto o score acerta.
- **Testes de coletor com respostas gravadas** (`vcrpy`), sem rede, mais um relatório semanal de saúde das fontes.
- **Ruff completo** (hoje só sintaxe) em commit de limpeza separado; `mypy` nos módulos novos.
- **PyPI:** `pip install tropeiro-intel` e entrada `tropeiro` na CLI.
- **README em inglês** e demonstração narrada (GIF de 30 s mostrando um caso do início ao STIX).
- **Trilha de auditoria do analista:** confirmar/descartar uma entidade da IA fica registrado (quem, quando, motivo) e vira evidência `analyst_confirmed`.

## Fase 2 · Inovação OSINT (2–3 meses)

Ideias pequenas, em Python simples, que ninguém entrega junto:

1. **Fingerprint de kit ao vivo:** coletar favicon, JS e CSS via urlscan e clusterizar domínios pelo mesmo kit (o módulo existe; falta a coleta).
2. **Linha do tempo de infraestrutura:** quando o domínio mudou de IP/NS/certificado, com Wayback, para provar reuso e rotatividade.
3. **Iscas BR por regra comunitária:** regras YAML de marca/tema (Receita, Correios, PIX, Detran, INSS, bancos) com validação por exemplos; qualquer pessoa contribui por PR.
4. **Pivô por contato:** telefone/WhatsApp/PIX da isca leva a outros casos da memória (só dados já observados, nunca consulta a pessoas).
5. **Detecção de reuso de texto entre campanhas** (similaridade de isca + traduções/variações), com a explicação do que foi comparado.
6. **Regras Sigma testadas:** gerar também o log de exemplo que deve disparar a regra, e validar na CI.
7. **Takedown pack:** pacote com evidência datada + hash + texto de abuse report por registrar/hosting.

## Fase 3 · Integração e escala (3–6 meses)

- **MISP / OpenCTI:** push opcional dos STIX/MISP já gerados (com TLP e `to_ids` conservador).
- **Adaptadores de detecção:** Wazuh, Elastic e Suricata a partir das regras Sigma.
- **API enxuta (FastAPI)** com os mesmos objetos, para outros times chamarem o Tropeiro.
- **Núcleo compartilhado com o Mineiro:** extrator de entidades BR, exportação STIX e normalização de IOC num pacote comum; pivô username/telefone (Mineiro) → campanha (Tropeiro).
- **Memória compartilhável:** exportar/importar bundle anonimizado de prevalência entre analistas.

## Métricas de sucesso

| Métrica | Hoje | Meta 3 meses |
|---|---|---|
| Casos reais anonimizados rotulados | 0 | 30 |
| Brier score publicado | — | < 0,20 |
| Módulos ligados ao Workbench | quase todos (falta fingerprint de kit e calibração) | todos |
| Cobertura de coletores com teste gravado | 0 | 100% |
| Instalação | clone + pip -e | `pip install tropeiro-intel` |

## O que não vira dependência central

Provedores pagos continuam adaptadores. O Colab público precisa funcionar sem assinatura, GPU ou banco externo. Nada derivado de IA escreve no Evidence Ledger.

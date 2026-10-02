# Documentação do Tropeiro Intel

Escolha o caminho pelo seu perfil. Todos os exemplos de comando e de Python desta pasta foram executados em CI (`tests/test_docs.py`).

## Por onde começar

| Eu sou... | Leia nesta ordem |
|---|---|
| **Nunca usei OSINT nem Colab** | [Guia para iniciantes](BEGINNER_GUIDE.md) → [Início rápido](QUICKSTART.md) → [Guia do Workbench](USER_GUIDE.md) → [FAQ](FAQ.md) |
| **Analista de phishing / CTI** | [Início rápido](QUICKSTART.md) → [Guia do Workbench](USER_GUIDE.md) → [Interpretando resultados](INTERPRETING_RESULTS.md) → [Receitas](COOKBOOK.md) |
| **SOC / Detecção** | [CLI](CLI.md) → [Saídas e formatos](OUTPUTS.md) → [Receitas](COOKBOOK.md#5-gerar-regras-de-detecção-e-ioc-para-o-tip) |
| **Desenvolvedor** | [Instalação](INSTALLATION.md) → [API Python](PYTHON_API.md) → [Arquitetura](ARCHITECTURE.md) → [Contribuindo](../CONTRIBUTING.md) |
| **Gestor / quer avaliar a ferramenta** | [README](../README.md) → [Matriz de recursos](FEATURE_MATRIX.md) → [Roadmap](ROADMAP.md) |

## Mapa completo

### Usar
| Documento | Para quê |
|---|---|
| [QUICKSTART](QUICKSTART.md) | três caminhos para a primeira investigação: Workbench local, CLI offline ou Colab |
| [USER_GUIDE](USER_GUIDE.md) | o Workbench aba por aba, com capturas de tela |
| [CLI](CLI.md) | `tropeiro lure` e `tropeiro workbench`, opções e códigos de saída |
| [COOKBOOK](COOKBOOK.md) | sete receitas passo a passo (domínio suspeito, isca em texto, lote de IOCs, memória, regras, takedown, automação) |
| [SEARCH_TYPES](SEARCH_TYPES.md) | cada tipo de alvo e o que o Tropeiro faz com ele |
| [COLAB](COLAB.md) | o notebook oficial e o assistente guiado |

### Configurar
| Documento | Para quê |
|---|---|
| [INSTALLATION](INSTALLATION.md) | Colab, instalação local, extras, GPU/CPU para IA, verificação |
| [CONFIGURATION](CONFIGURATION.md) | modos, profundidade, chaves de API, cache, limite por host, memória, variáveis de ambiente |

### Entender
| Documento | Para quê |
|---|---|
| [INTERPRETING_RESULTS](INTERPRETING_RESULTS.md) | BLOCK/HUNT/MONITOR, bandas de confiança, derivado vs. observado, armadilhas |
| [OUTPUTS](OUTPUTS.md) | cada arquivo exportado, campos principais e como importar em MISP/OpenCTI/SIEM |
| [AI](AI.md) | extração híbrida, correlação e verificação das respostas do Qwen |
| [INTELLIGENCE_MODEL](INTELLIGENCE_MODEL.md) · [ATTRIBUTION](ATTRIBUTION.md) · [ACTIONABLE_INTELLIGENCE](ACTIONABLE_INTELLIGENCE.md) · [CAMPAIGN_MEMORY](CAMPAIGN_MEMORY.md) | o modelo analítico por trás |
| [GLOSSARY](GLOSSARY.md) | termos de OSINT, CTI e do projeto |
| [REPORTING_UX](REPORTING_UX.md) | como o relatório HTML é organizado |

### Resolver problemas
| Documento | Para quê |
|---|---|
| [FAQ](FAQ.md) | perguntas frequentes (privacidade, custo, precisão, limites) |
| [COMMON_ERRORS](COMMON_ERRORS.md) | erros comuns, com causa e correção |
| [TROUBLESHOOTING](TROUBLESHOOTING.md) | fontes vazias, lentidão, runtime reiniciado |

### Desenvolver
| Documento | Para quê |
|---|---|
| [PYTHON_API](PYTHON_API.md) | uso de cada módulo como biblioteca, com exemplos executáveis |
| [ARCHITECTURE](ARCHITECTURE.md) · [DATA_MODEL](DATA_MODEL.md) · [FRONTEND](FRONTEND.md) | estrutura interna |
| [ROADMAP](ROADMAP.md) · [FEATURE_MATRIX](FEATURE_MATRIX.md) · [PUBLIC_RELEASE](PUBLIC_RELEASE.md) | o que existe, o que vem e o histórico da primeira versão pública |

## Convenções

- **Passivo por padrão.** Nada aqui orienta consulta a dados privados de pessoas.
- **Correlação não é identidade.** Um achado é uma observação.
- Valores de exemplo usam domínios `.example` e IPs de documentação (`203.0.113.0/24`).

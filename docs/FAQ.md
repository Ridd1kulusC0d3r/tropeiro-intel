# Perguntas frequentes

## Geral

**O que o Tropeiro faz, em uma frase?**
Recebe um domínio, URL, IP ou o texto de uma isca, coleta fontes públicas, organiza a evidência, mostra o que sustenta (e o que não), e exporta para MISP/STIX/Sigma.

**Serve para encontrar dados de uma pessoa?**
Não, e foi desenhado para não servir. E-mail e telefone são tratados **só como IOCs já observados** numa investigação defensiva. Não há busca reversa de pessoa, endereço ou identidade.

**Precisa pagar alguma API?**
Não. O núcleo roda sem chaves. Chaves opcionais (VirusTotal, ThreatFox, FOFA, Censys, DNSDumpster) ampliam a coleta. Veja [CONFIGURATION](CONFIGURATION.md#chaves-de-api-todas-opcionais).

**Posso usar offline?**
Sim, em parte: a CLI e a API Python de extração, decisão e exportação funcionam sem rede. A coleta (DNS, RDAP, certificados, scans) precisa de internet.

**Qual a diferença entre Workbench, notebook e CLI?**
Workbench: interface local, rápida, com grafo e exportações. Notebook: investigação completa guiada (Wayback, VirusTotal, lookalikes). CLI: análise offline do texto de uma isca. Tabela em [CONFIGURATION](CONFIGURATION.md#o-que-liga-em-cada-superfície).

## Privacidade e segurança

**O texto da isca sai do meu computador?**
Não. A extração (regras e modelos) é local. Com a Campaign Memory ligada, o texto fica guardado no banco local para comparar iscas (nunca no `case.json` exportado); desmarque a memória para não guardar. As consultas de coleta usam apenas **domínios/hostnames** extraídos. `--share` do Workbench cria um link público temporário: evite com casos reais.

**Posso colar uma mensagem com dados pessoais da vítima?**
Evite. Remova nomes, CPFs e telefones das vítimas antes de colar quando possível, e não os inclua em pacotes compartilhados. CPFs que aparecem na isca são extraídos para análise local, não são consultados em lugar nenhum.

**O Tropeiro acessa o site malicioso?**
Não por padrão. O modo é passivo. A sondagem direta exige `AUTHORIZED_ACTIVE` **e** `enable_http_probe=True`, e é só para ativos seus ou autorizados.

## Resultados

**Por que um domínio claramente de phishing deu `MONITOR`?**
Poucas fontes independentes ou sem atividade recente. O Tropeiro só recomenda `BLOCK` com ≥ 2 famílias de fonte, ≥ 3 evidências e atividade. Veja [INTERPRETING_RESULTS](INTERPRETING_RESULTS.md#decisão-por-ioc).

**A fonte deu `UNAVAILABLE`. E agora?**
Pode ser timeout, cota ou mudança de formato. Tente de novo; veja [TROUBLESHOOTING](TROUBLESHOOTING.md). O resultado "vazio" nunca significa "benigno".

**Posso confiar na marca que a regra identificou?**
As regras são palavras-chave editáveis: boas para triagem, não para veredito. Lista vazia não prova legitimidade.

**A IA pode inventar evidência?**
Não entra no Evidence Ledger. As referências do Qwen são validadas contra o ledger; achado sem referência válida é rebaixado a hipótese. As entidades da IA começam como "não confirmadas".

**Por que `wa.me` não virou regra de bloqueio?**
Porque bloquear o WhatsApp inteiro quebra usuários e não detém a campanha. O IOC útil é o número. Veja [Plataformas legítimas](INTERPRETING_RESULTS.md#plataformas-legítimas).

**Duas campanhas compartilham um IP. É o mesmo operador?**
Não necessariamente. Hospedagem compartilhada explica. O Tropeiro pesa o que é raro e marca `same_operator_inferred = false`.

## Técnico

**Quais versões de Python?**
3.10 a 3.13 (testadas em CI).

**Onde ficam os dados?**
Casos: `<base>/tropeiro_ui_<ID>/`. Memória: `~/.tropeiro/tropeiro_case_memory.sqlite` (local) ou `/content/...` (Colab). Veja [CONFIGURATION](CONFIGURATION.md).

**Como atualizo as regras de marca?**
[CONFIGURATION](CONFIGURATION.md#regras-de-iscas-brasileiras): `load_rules("arquivo.json")`.

**O Workbench respeita modo e profundidade?**
Sim, desde a 4.7. Veja a tabela em [CONFIGURATION](CONFIGURATION.md#o-que-liga-em-cada-superfície).

**Como contribuo?**
[CONTRIBUTING](../CONTRIBUTING.md).

## Limites conhecidos

- GLiNER e Qwen foram executados de verdade em CPU (veja [AI](AI.md#validação-com-modelos-reais)), mas só sobre iscas de exemplo, não sobre casos reais.
- Importação em MISP/OpenCTI segue os formatos padrão, mas não foi testada contra instâncias reais.
- Cobertura de iscas: lista curta de marcas brasileiras; contribuições são bem-vindas.
- Fingerprint de kit e calibração existem como bibliotecas, ainda não como telas do Workbench (lotes de registro e iscas parecidas já têm a aba **Campanha**).

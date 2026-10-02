# Glossário rápido

**IOC** — indicador observado, como domínio, URL, IP ou hash.

**Seed** — ponto inicial da investigação. No modo guiado você não precisa usar este termo; basta preencher o campo de alvo.

**DNS** — sistema que liga nomes de domínio a infraestrutura.

**RDAP** — protocolo padronizado para dados públicos de registro de domínios/IPs.

**CT / Certificate Transparency** — registros públicos de certificados TLS.

**ASN** — número que identifica uma rede/autonomous system.

**Passive DNS** — histórico de resoluções DNS observado por terceiros.

**Lookalike** — domínio visual/lexicalmente parecido com outro. Similaridade não significa malicioso.

**Pivot** — novo caminho de investigação descoberto a partir de uma evidência.

**Evidence Ledger** — registro de evidências com origem/provenance.

**Source Health** — painel que informa quais fontes executaram, foram puladas ou falharam.

**Campaign Cluster** — grupo de artefatos relacionados por evidências; não significa automaticamente mesmo operador.

**Operator Correlation** — avaliação de possível controle operacional comum.

**Attribution** — associação sustentada por evidências; exige rigor maior que simples correlação.

**ACH** — Analysis of Competing Hypotheses; compara explicações alternativas para reduzir confirmation bias.

**Actionability** — quão apropriado é agir operacionalmente sobre um IOC.

**False Positive / FP** — risco de atingir infraestrutura legítima ao interpretar ou bloquear um indicador.

**SKIPPED** — módulo não executado por configuração, falta de chave, budget ou irrelevância. Não significa erro.

**UNAVAILABLE** — módulo tentou executar, mas a fonte não respondeu corretamente.

## Formatos e padrões

**Defang / refang** — defang altera um IOC para que não seja clicável (`hxxps://x[.]com`); refang desfaz. O Tropeiro faz refang automaticamente na entrada.

**TLP** — Traffic Light Protocol: `WHITE/CLEAR`, `GREEN`, `AMBER`, `RED`; define com quem a informação pode ser compartilhada.

**STIX 2.1** — formato aberto de inteligência de ameaças. No Tropeiro: `Indicator`, `Campaign`, observáveis e `Relationship`.

**Indicator (STIX)** — regra/padrão que identifica algo malicioso, com período de validade.

**MISP** — plataforma de compartilhamento de inteligência. `to_ids` indica se o atributo pode ser usado em detecção/bloqueio automático.

**Sigma** — formato aberto de regras de detecção que converte para vários SIEMs.

**TIP** — Threat Intelligence Platform (MISP, OpenCTI etc.).

## Conceitos do Tropeiro

**Observado × derivado** — observado: uma fonte respondeu. Derivado: calculado a partir de observações (similaridade, ligação da IA). Derivado é indício.

**Plataforma legítima** — serviço comum (WhatsApp, Google) que aparece na isca; é contexto, não alvo de bloqueio.

**Campaign Memory** — banco local de casos anteriores, com prevalência e raridade de artefatos.

**Prevalência / raridade** — quão comum um artefato é nos seus casos. Comum pesa pouco; raro pesa muito.

**Fingerprint de kit** — assinatura dos arquivos estáticos de um kit de phishing; domínios com o mesmo kit podem ser da mesma campanha.

**Lote de registro** — domínios criados em sequência, no mesmo registrar e nameservers.

**Banda de confiança** — `HIGH`, `MODERATE`, `LOW`, `INSUFFICIENT`.

**Brier score** — erro quadrático médio entre a probabilidade prevista e o resultado real (0 = perfeito; 0,25 = chute 50%).

## IA

**GLiNER** — modelo que extrai entidades nomeadas (organização, marca...) sem treino específico. Roda local.

**Qwen** — modelo de linguagem usado para resumir a evidência do caso; só enxerga o pacote de evidência e tem as citações validadas.

**Evidence packet** — o recorte do caso entregue ao modelo, com hash SHA-256.

## Brasil

**CPF / CNPJ** — documentos de pessoa física/jurídica; o Tropeiro só aceita os que passam no dígito verificador.

**PIX** — pagamento instantâneo do Banco Central. **Chave aleatória (EVP)** é um UUID; **copia-e-cola** é o código `000201...` do QR.

**Receita Federal, Correios, Detran, INSS** — marcas frequentemente imitadas em iscas.

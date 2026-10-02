# Interpretando os resultados

A pergunta que o Tropeiro responde não é "isto é malicioso?", e sim **"o que a evidência sustenta, com que força, e o que ainda falta?"**.

## Regra de ouro

Um resultado de ferramenta é uma **observação**, não uma conclusão. Domínio parecido, mesmo IP ou mesmo ASN não prova que dois ativos são do mesmo operador.

## Observado, derivado e inferido

| Rótulo | De onde vem | Como tratar |
|---|---|---|
| **observado** | uma fonte respondeu (DNS, RDAP, certificado, scan) | fato sobre a fonte, com a confiabilidade dela |
| **derivado** | calculado a partir de observações (similaridade, relação proposta) | indício; confirme antes de agir |
| **IA (REGRA / GLiNER / Qwen)** | extração e análise automáticas | **candidato**; `analyst_confirmed` começa `False` e nada disso entra no Evidence Ledger |

## Decisão por IOC

A decisão sai de `build_ioc_decisions` com esta política (`DEFAULT_POLICY`):

| Decisão | Condições (todas) |
|---|---|
| **BLOCK** | `actionability ≥ 0,85` **e** ativo agora **e** tipo `domain` ou `url` **e** ≥ 2 famílias de fonte **e** ≥ 3 evidências **e** nenhum aviso de severidade alta |
| **TAKEDOWN_CANDIDATE** | `actionability ≥ 0,78` **e** ativo **e** `domain`/`url` **e** ≥ 2 famílias de fonte |
| **HUNT** | `actionability ≥ 0,55` (vale caçar nos seus logs) |
| **MONITOR** | `actionability ≥ 0,35` |
| **DO_NOT_BLOCK** | abaixo de 0,35 **e** há aviso (resolver público, CDN, host compartilhado, lista MISP) |
| **INSUFFICIENT_EVIDENCE** | o resto |

`actionability` = confiança − penalidade dos avisos (baixa = 0,05, média = 0,20, alta = 0,45; teto 0,80). Os limiares podem ser trocados: `build_ioc_decisions(iocs, policy={"block_actionability": 0.9})`.

> **"Pedi BLOCK e apareceu HUNT."** É intencional: o Tropeiro exige evidência, atividade, diversidade de fontes e controle de falso positivo antes de recomendar bloqueio. Um IOC que só aparece em uma família de fonte nunca vira BLOCK.

### Bandas de confiança

| Banda | Faixa |
|---|---|
| `HIGH` | ≥ 0,85 |
| `MODERATE` | ≥ 0,65 |
| `LOW` | ≥ 0,40 |
| `INSUFFICIENT` | abaixo disso |

No Workbench rápido, a confiança inicial de cada IOC é conservadora (teto de 0,55) porque ele só reúne evidência básica: espere `MONITOR`/`HUNT`, não `BLOCK`. Para chegar a `BLOCK`, o caso precisa de várias fontes independentes e atividade recente.

### Risco de falso positivo

`LOW`/`MEDIUM`/`HIGH`. **HIGH** quando o indicador cai em infraestrutura comum (resolver público, CDN, hospedagem compartilhada) ou tem pouca sustentação. Nunca bloqueie IOC com FP alto sem validar.

## Plataformas legítimas

Domínios como `wa.me`, `whatsapp.com`, `t.me`, `google.com`, `facebook.com`, `gov.br` aparecem em iscas, mas **não são o IOC**. O Tropeiro os marca **PLATAFORMA LEGÍTIMA** e os exporta só como contexto. O que importa é o número/conta/URL específica (por exemplo, o telefone do WhatsApp). URLs específicas em outras plataformas (um formulário hospedado) continuam acionáveis por URL.

## Ligações propostas pela IA

| Relação | Significa | Força |
|---|---|---|
| `same_value` | o valor extraído da isca é idêntico a uma entidade já coletada | 1,0 |
| `same_root_domain` | mesmo domínio registrável (subdomínios irmãos) | 0,7 |
| `similar_name` | nome parecido (`token_set_ratio ≥ 88`) com org/marca/registrar | proporcional |

O `score` multiplica a confiança da extração pela força da ligação. É para **priorizar revisão**, nunca prova.

## Fontes: `OK`, `SKIPPED`, `UNAVAILABLE`

| Status | Leitura |
|---|---|
| `OK` | rodou |
| `SKIPPED_MISSING_SECRET` | falta a chave (opcional): não é erro |
| `SKIPPED_BUDGET` | fora da profundidade escolhida |
| `NOT_NEEDED` | a fonte não se aplica a este tipo de alvo |
| `UNAVAILABLE` | tentou e falhou (timeout, cota, mudança de formato) |

**Ausência de resultado não é "benigno".** Pode ser domínio novo, fonte que não indexa aquilo, cota esgotada ou timeout. Sempre olhe a saúde das fontes antes de concluir algo pela falta de dados.

## Campaign Memory: prevalência e raridade

Cada artefato recebe frequência nos seus casos anteriores. **Comum** (ex.: um IP de nuvem) pesa pouco; **raro** (um identificador de kit, um registrante específico) pesa muito. Todo casamento traz `same_operator_inferred = false`: semelhança entre casos é **hipótese de trabalho**, nunca atribuição automática.

## Atribuição: o que cada nível autoriza dizer

| Nível | Pode afirmar | Não pode afirmar |
|---|---|---|
| Relação de infraestrutura | "compartilham IP/NS/registrar" | que são do mesmo operador |
| Pertencimento à campanha | "mesma campanha provável" (vários sinais raros) | quem é o operador |
| Mesmo operador | exige evidência independente e discriminante | identidade real |

O Tropeiro compara hipóteses concorrentes (mesmo operador × mesmo kit × mesma hospedagem × revendedor × coincidência). Veja [ATTRIBUTION](ATTRIBUTION.md).

## Armadilhas comuns

| Armadilha | Correção |
|---|---|
| "Mesmo IP, logo mesmo operador" | hospedagem compartilhada explica; olhe o que é raro |
| "Nada encontrado, logo seguro" | confira a saúde das fontes |
| "A IA citou, logo é verdade" | só vale com `evidence_id` válido; achado sem referência é rebaixado a hipótese |
| "Bloquear o domínio da plataforma" | bloqueie o IOC específico, não `wa.me`/`google.com` |
| "Tratar `.example` do demo como real" | o caso de demonstração é fictício |
| "Reaproveitar a decisão semanas depois" | revalide: veja `expiration_guidance` |

# Camada de IA

Princípio: **IA propõe, evidência decide.** Nada gerado por modelo entra no Evidence Ledger.

## Pipeline de extração (`tropeiro.ai.extract_hybrid`)

1. **Refang** (`hxxp`, `[.]`, `(dot)`, `[@]`) para que regras e modelos vejam o IOC real.
2. **Regras determinísticas** (sempre rodam, sem modelo): URLs, domínios, IPs, e-mails, telefones, hashes, CPF/CNPJ com dígito verificador, chave PIX aleatória, PIX copia-e-cola, WhatsApp, marca/tema da isca (Receita, Correios, PIX, Detran, INSS...).
3. **GLiNER** (opcional) acrescenta entidades de contexto: organização, marca, registrar, hospedagem, família de malware, alias de ator.
4. **Validação**: saída do modelo do tipo domínio/IP/e-mail/URL/telefone só é aceita se for válida. `999.999.1.1` e `nao e dominio!!` são descartados.
5. **Concordância**: entidade confirmada por regra **e** modelo ganha +0,08 de score; só-modelo mantém o score do modelo.

Toda entidade sai com `derived=True` e `analyst_confirmed=False`.

## Correlação (`correlate_entities`, `lure_similarity`)

Liga candidatos a entidades já coletadas no caso:

| relação | critério | força |
|---|---|---|
| `same_value` | valor idêntico | 1.0 |
| `same_root_domain` | mesmo domínio registrável (subdomínios irmãos) | 0.7 |
| `similar_name` | `token_set_ratio ≥ 88` (org/marca/registrar) | proporcional |

`lure_similarity` compara o texto da isca com iscas de outros casos (útil quando não há IOC em comum). No grafo, estas ligações aparecem **tracejadas**.

## Análise com Qwen (`run_qwen_analysis`)

- o modelo só enxerga o `EVIDENCE_PACKET` (hash SHA-256 registrado) e recebe a **lista de `evidence_id` válidos** para citar;
- a geração é **determinística por padrão** (`QwenLocalChat(deterministic=True)`): o mesmo prompt dá a mesma resposta. Use `deterministic=False` para amostragem;
- se a resposta não for JSON válido, há **uma** nova tentativa pedindo apenas o JSON (`OK_RETRY`);
- referências a `evidence_id` inexistentes são removidas (`validate_ai_analysis`);
- achado `observed` ou de confiança alta **sem referência válida** é rebaixado para `hypothesis` / `INSUFFICIENT` (`enforce_evidence_support`), com contagem em `_validation.downgraded_findings`;
- **referência válida não basta**: se a afirmação não fala da evidência citada (nenhuma palavra em comum com a entidade, o valor ou a fonte), o achado é marcado `evidence_mismatch`, rebaixado para `hypothesis` / `LOW` e contado em `_validation.mismatched_findings`. Isso nasceu de um caso real: o Qwen3-0.6B citou um `evidence_id` existente para uma afirmação sem relação com ele;
- hipótese que usa a mesma referência como apoio **e** contradição perde a contradição (`refs_overlap`);
- `attach_ai_overlay` aborta se o ledger mudar.

## Modelos

| Papel | Padrão | Observação |
|---|---|---|
| Entidades | `urchade/gliner_multi-v2.1` | multilíngue; CPU ok |
| Análise | `Qwen/Qwen3-0.6B` (CPU) · `Qwen3-1.7B` (GPU) | escolhido por `runtime_profile()` |

No Workbench, **IA = OFF** ainda executa as regras; GLiNER/Qwen só acrescentam.

## Validação com modelos reais

GLiNER e Qwen foram executados de verdade, pelo caminho completo do Workbench (`IA = GLINER_QWEN`), com as fontes de rede simuladas como indisponíveis e a isca [`examples/lure_receita.txt`](../examples/lure_receita.txt).

| | |
|---|---|
| Ambiente | só CPU (sem GPU), Python 3.11, `torch` 2.14, `transformers` 5.16 |
| Modelos | `urchade/gliner_multi-v2.1` e `Qwen/Qwen3-0.6B` |
| GLiNER | carga 9,5 s (depois do download); extração híbrida 0,3 s por isca |
| Caso completo com Qwen | **58 a 101 s** em CPU (cinco execuções) |
| O que o GLiNER acrescentou | a organização **"Banco Aurora S.A."** (score 0,92), que as regras não reconhecem |
| Determinismo | com o mesmo prompt, duas execuções deram **saída idêntica** em modo determinístico e **saídas diferentes** em modo com amostragem |

### O que a execução real revelou (e foi corrigido)

| # | Problema encontrado | Correção |
|---|---|---|
| 1 | O GLiNER não carregava no `transformers` recente: faltavam `sentencepiece` e `protobuf` no extra `ai` | extra `ai` completo |
| 2 | O Qwen citou um `evidence_id` **existente** para uma afirmação sem relação com ele ("seu CPF está irregular", marcada `observed`/`HIGH`, com justificativa inventada) | checagem de coerência: afirmação sem relação com a evidência vira `hypothesis`/`LOW` (`evidence_mismatch`) |
| 3 | O modelo copiou o placeholder `EV-ID` do schema | o prompt lista os ids válidos; ids inválidos continuam sendo removidos |
| 4 | Hipótese **sem nenhuma referência** com confiança `HIGH` | vira `INSUFFICIENT` (`no_support`) |
| 5 | Respostas diferentes a cada execução | geração determinística por padrão |

Resultado final com o código atual, na mesma isca: o achado sem relação saiu como `hypothesis`/`LOW` e a hipótese como `INSUFFICIENT`.

### O que ainda **não** é garantido

- **Ideias de detecção** (`detection_opportunities`) só têm a referência checada. O Qwen3-0.6B sugeriu "identificar e validar o CPF no DNS", que cita evidência válida mas **não faz sentido**. Trate esse campo como rascunho.
- O 0,6B é um modelo **pequeno**: a análise é fraca mesmo com as proteções. A interface avisa ("modelo pequeno: revise sempre"). Use o Qwen3-1.7B em GPU para um resultado melhor.
- **Não testado:** GPU, Qwen3-1.7B, casos reais anonimizados e a qualidade em português em escala. Registre o que observar em uma issue.
- A verificação é uma heurística lexical conservadora: ela pega afirmações **sem nenhuma relação** com a evidência, não erros sutis.

Por isso a regra de ouro continua: **a IA propõe; a evidência e o analista decidem.**

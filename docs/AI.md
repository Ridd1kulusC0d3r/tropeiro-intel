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

- o modelo só enxerga o `EVIDENCE_PACKET` (hash SHA-256 registrado);
- se a resposta não for JSON válido, há **uma** nova tentativa pedindo apenas o JSON (`OK_RETRY`);
- referências a `evidence_id` inexistentes são removidas (`validate_ai_analysis`);
- achado `observed` ou de confiança alta **sem referência válida** é rebaixado para `hypothesis` / `INSUFFICIENT` (`enforce_evidence_support`), com contagem em `_validation.downgraded_findings`;
- `attach_ai_overlay` aborta se o ledger mudar.

## Modelos

| Papel | Padrão | Observação |
|---|---|---|
| Entidades | `urchade/gliner_multi-v2.1` | multilíngue; CPU ok |
| Análise | `Qwen/Qwen3-0.6B` (CPU) · `Qwen3-1.7B` (GPU) | escolhido por `runtime_profile()` |

No Workbench, **IA = OFF** ainda executa as regras; GLiNER/Qwen só acrescentam.

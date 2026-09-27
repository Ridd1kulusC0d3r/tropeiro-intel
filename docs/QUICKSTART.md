# Quick Start — Guided Investigation

Este fluxo foi escrito para alguém que nunca usou Colab.

## 1. Abra o notebook oficial

[Open in Google Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)

**Não use Run all imediatamente.** Primeiro configure o alvo na etapa 04.

## 2. Execute 01 · Bootstrap

Clique em ▶ e espere a confirmação de que o backend foi importado.

## 3. Execute 02 · Health Check

Procure:
- `repo: true`;
- versão do Tropeiro;
- caminho em `/content/tropeiro-intel`;
- `Runtime saudável`.

## 4. Use o Assistente Guiado

Na etapa 04:

1. escolha **Detectar automaticamente** ou o tipo;
2. cole o alvo;
3. confirme que o campo mudou para Domínio, URL, IP, E-mail, Hash, Telefone ou Texto da isca;
4. mantenha `PASSIVE` na primeira investigação;
5. escolha `balanced`.

Exemplo:

```text
Tipo: Domínio
Alvo: dominio-suspeito.com
Modo: PASSIVE
Profundidade: balanced
```

## 5. Mantenha o plano automático

Na etapa 05 deixe marcado:

```text
Usar plano automático recomendado
```

O Tropeiro calcula o plano com base em tipo de IOC, modo, budget, secrets, marca e número de alvos.

## 6. Continue em ordem

Antes de **cada célula executável** existe uma caixa `🧭 Antes de executar` com:
- objetivo;
- como usar;
- saída esperada;
- recuperação de erro;
- erros comuns;
- indicação se você pode continuar.

## 7. Entenda os status

| Status | Significado |
|---|---|
| OK | executou |
| READY | disponível |
| SKIPPED | pulado por configuração |
| SKIPPED_MISSING_SECRET | faltou API key opcional |
| SKIPPED_BUDGET | não entra na profundidade |
| NOT_NEEDED | não é necessário neste caso |
| UNAVAILABLE | tentou executar e falhou |

## 8. Leia o resultado

1. Executive Assessment
2. Action Matrix
3. IOC Decisions
4. Campaign / Relationship Graph
5. Attribution / ACH
6. Collection Gaps
7. Next Best Pivots
8. Evidence Ledger
9. Source Health

## 9. Relatório e export

O relatório HTML pode ser gerado mesmo com módulos opcionais ausentes. Um caso incompleto é marcado como relatório parcial.

## 10. Ajuda

- [Guia para iniciantes](BEGINNER_GUIDE.md)
- [Tipos de busca](SEARCH_TYPES.md)
- [Erros comuns](COMMON_ERRORS.md)
- [Glossário](GLOSSARY.md)

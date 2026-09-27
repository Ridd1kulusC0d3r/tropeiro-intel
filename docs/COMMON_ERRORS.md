# Erros comuns no Colab

## `ModuleNotFoundError: No module named 'tropeiro'`

**Significa:** o backend não carregou.

**Faça:**
1. Runtime → Disconnect and delete runtime.
2. Abra novamente o notebook oficial.
3. Execute a célula 01.
4. Confirme a célula 02.

## `NameError: REPORT_DATA is not defined`

Versões atuais reconstruem o contexto do relatório automaticamente. Se aparecer:
- confira se o notebook e o backend são da mesma versão;
- reinicie o runtime;
- execute 01, 02 e depois as etapas em ordem.

## `SKIPPED_MISSING_SECRET`

Não é falha. A API é opcional e a chave não foi configurada.

## `UNAVAILABLE`

A fonte tentou rodar e falhou. Pode ser:
- timeout;
- serviço externo fora do ar;
- quota;
- autenticação;
- mudança de schema.

Confira **Source Health**.

## Tabela vazia

Uma tabela vazia pode ser resultado válido. Exemplos:
- domínio novo sem histórico;
- nenhum lookalike registrado;
- nenhuma evidência de takeover;
- nenhum scan público.

Não transforme ausência de resultado em “benigno”.

## Relatório não aparece dentro do iframe

Colab pode bloquear ou recusar algumas formas de `localhost`. Use o arquivo HTML gerado pelo Export Center. O relatório é local/offline e não precisa de servidor web.

## dnstwist demora muito

Reduza a profundidade para `free` ou diminua o limite avançado. A versão guiada ajusta o limite automaticamente ao número de alvos.

## Provider pede API key

Abra o ícone de chave do Colab e adicione o secret exatamente com o nome documentado. Providers pagos não são obrigatórios.

## O notebook parece travado

Algumas consultas externas levam tempo. Espere a célula finalizar antes de clicar novamente. Se um provider ficar indisponível, o pipeline deve registrar o status e continuar.

## Pedi BLOCK e apareceu MONITOR/HUNT

Isso é intencional. O Tropeiro exige evidência, atividade, diversidade de fontes e controle de falso positivo antes de recomendar enforcement.

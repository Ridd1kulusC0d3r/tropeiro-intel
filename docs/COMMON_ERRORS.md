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

---

# Erros comuns no Workbench e na CLI

## `ModuleNotFoundError: No module named 'gradio'`

Instalou sem o extra do Workbench. Rode `pip install -e ".[colab]"`.

## Workbench abre sem o tema escuro (texto claro em fundo claro)

Costuma ser Gradio incompatível ou o app aberto por `build_app().launch()` no Gradio 6 (o tema é aplicado no `launch()`). Abra com `tropeiro workbench` (ou `launch_local()` / `launch_colab_frontend()`) e use `gradio>=4.44,<7`.

## `tropeiro: command not found`

Ambiente virtual inativo ou instalação sem `-e`. Ative o venv, ou use `python -m tropeiro.cli ...`.

## `ValueError: hostname inválido: '...'`

O alvo tem `/`, `?`, `&`, espaço ou não é um domínio válido. Passe só o domínio (`exemplo.com`) ou use o tipo `URL`/`LURE_TEXT` para o texto completo.

## A CLI lista só o domínio de uma plataforma (ex.: `wa.me`) e não o do golpe

Versões anteriores à 4.6.1 não faziam refang na CLI: `hxxps://x[.]example` não era lido. Atualize (`git pull && pip install -e .`).

## Aparece `somente_contexto` com o domínio que eu queria bloquear

O domínio está na lista de plataformas legítimas (`tropeiro/intelligence/legit_domains.py`). Bloquear `google.com`/`wa.me` inteiro quebra usuários. Bloqueie a URL específica ou o número, não a plataforma.

## `lures` vem vazio

Nenhuma regra de marca/tema bateu. Não significa que a mensagem seja legítima. Adicione suas regras ([CONFIGURATION](CONFIGURATION.md#regras-de-iscas-brasileiras)).

## Caso rápido sem data de registro

Versões anteriores à 4.6.1 não gravavam `rdap:created` no ledger. Atualize.

## Busca de texto de isca não consultou nada (tratada como telefone)

Versões anteriores à 4.8 classificavam um texto com um número de telefone como **Telefone**, e nenhuma fonte rodava. Atualize: agora um texto com palavras é sempre uma **isca**. Veja [SEARCH_TYPES](SEARCH_TYPES.md#como-o-tipo-é-detectado).

## A tela do Workbench ficou sem resultado e sem erro (`InvalidPathError` no terminal)

O Gradio só serve arquivos da pasta atual, da temporária ou de `allowed_paths`. Até a 4.7 os arquivos exportados ficavam em uma pasta fora disso e a tela não exibia nada. Na 4.8 o Workbench publica cópias numa pasta aceita e libera a pasta de trabalho. Atualize.

## `HTTP 403` no urlscan (detalhes)

A API de resultados do urlscan pode exigir chave. A consulta é interrompida após 2 falhas seguidas e o estado fica `UNAVAILABLE` apenas para `urlscan:detalhes`; a busca do urlscan segue `OK`. Defina `URLSCAN_API_KEY` se precisar dos detalhes.

## `TIMEOUT` em alguma fonte

O prazo total (45/90/180 s) acabou antes da fonte responder. O resultado sai parcial. Aumente a profundidade ou use `--deadline`.

## Memória "some" entre sessões do Colab

O arquivo padrão fica em `/content` e é apagado com o runtime. Aponte para o Drive ([CONFIGURATION](CONFIGURATION.md#campaign-memory)).

## Muitas fontes `UNAVAILABLE` ao mesmo tempo

Provável limite de taxa ou rede bloqueada. Aumente o intervalo (`http.MIN_INTERVAL = 2.0`), ligue o cache (`http.set_cache(...)`) e tente de novo.

## GLiNER: `SentencePieceExtractor requires the protobuf library` / `tiktoken is required to read a tiktoken file`

O tokenizador do GLiNER multilíngue (mDeBERTa) precisa de `sentencepiece` e `protobuf` com o `transformers` recente. O extra `ai` os instala a partir da 4.7; antes, rode `pip install sentencepiece protobuf` e reinicie o runtime.

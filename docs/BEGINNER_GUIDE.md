# Tropeiro Intel — Guia para quem está começando

Este guia assume **zero experiência com OSINT, Python ou Google Colab**. Você não precisa saber programar para executar o fluxo padrão.

## O que é o Tropeiro Intel?

É uma estação defensiva de investigação que recebe um IOC ou texto de isca, coleta fontes públicas/passivas, organiza evidências e produz um relatório.

Um **IOC** é um indicador observado durante uma investigação, como:

- domínio;
- URL;
- endereço IP;
- hash de arquivo;
- e-mail observado em uma campanha;
- telefone observado em uma campanha.

O Tropeiro não deve ser usado para procurar dados privados de pessoas.

## Primeiro uso em 7 passos

1. Abra o notebook oficial pelo botão **Open in Colab**.
2. Execute a célula **01 · Bootstrap**.
3. Execute **02 · Health Check** e confirme que aparece `Runtime saudável`.
4. Na célula **04 · Assistente guiado**, escolha o tipo de busca ou deixe **Detectar automaticamente**.
5. Cole seu alvo no campo que muda de nome: **Domínio**, **URL**, **IP**, **E-mail**, **Hash**, **Telefone** ou **Texto da isca**.
6. Na célula **05**, mantenha **Usar plano automático recomendado**.
7. Continue executando as células em ordem. Leia a caixa **Antes de executar** que aparece imediatamente antes de cada etapa.

## O botão ▶

Cada bloco de código tem um botão triangular ▶ na esquerda. Clique nele uma vez e espere terminar.

- `[ ]` significa que ainda não rodou;
- um círculo girando significa que está executando;
- um ✓/tempo significa que terminou;
- texto vermelho significa erro.

Não clique repetidamente enquanto a célula ainda está executando.

## Qual tipo escolher?

Veja [SEARCH_TYPES.md](SEARCH_TYPES.md). Se tiver dúvida, deixe **Detectar automaticamente**.

## Qual modo usar?

### PASSIVE
Use este modo quase sempre. Trabalha com fontes públicas/passivas.

### SAFE_ENRICHMENT
Consulta mais fontes opcionais, ainda sem sondagem direta do alvo.

### AUTHORIZED_ACTIVE
Somente para ativos em que você possui autorização explícita. Selecionar esse modo não liga automaticamente a sonda HTTP.

## O que significa SKIPPED?

Normalmente não é erro.

- `SKIPPED_MISSING_SECRET`: você não configurou uma API key opcional.
- `SKIPPED_BUDGET`: sua profundidade escolhida não inclui aquele provider.
- `DISABLED`: o módulo foi desativado.
- `NOT_NEEDED`: aquela fonte não é necessária para o tipo de busca.
- `UNAVAILABLE`: a fonte tentou executar e não respondeu corretamente.

## API keys são obrigatórias?

Não. O fluxo principal funciona sem providers pagos. Chaves extras apenas ampliam a coleta.

## O que não devo colar?

Nunca coloque:

- senhas;
- tokens;
- cookies de sessão;
- documentos pessoais;
- dados pessoais desnecessários;
- informações confidenciais que não devem ser enviadas a serviços públicos.

## Se der erro

1. Leia a caixa de ajuda imediatamente acima da célula.
2. Procure a **última linha vermelha** do erro.
3. Veja [COMMON_ERRORS.md](COMMON_ERRORS.md).
4. Confira a célula **Source Health** no final.
5. Se o backend não importar, reinicie o runtime e execute novamente a célula 01.

## Ordem para ler o resultado

1. Executive Assessment
2. Action Matrix
3. IOC Decisions
4. Campaign / Relationship Graph
5. Attribution / ACH
6. Collection Gaps
7. Next Best Pivots
8. Evidence Ledger
9. Source Health

## Regra de ouro

Um resultado de ferramenta é uma **observação**, não uma conclusão. Domínio parecido, mesmo IP ou mesmo ASN não prova que dois ativos pertencem ao mesmo operador.

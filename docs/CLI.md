# Linha de comando

A CLI funciona **100% offline**: não consulta nenhuma fonte, só analisa o que você fornece. É ideal para triagem rápida, scripts e CI.

```text
tropeiro lure ARQUIVO [--case ID] [--tlp COR] [--out DIR]
tropeiro workbench [--port N] [--share]
```

Sem instalar o comando: `python -m tropeiro.cli ...`.

## `tropeiro lure`: analisar o texto de uma isca

Lê uma mensagem (arquivo, ou `-` para a entrada padrão), identifica marca/tema, extrai IOCs e, com `--out`, exporta STIX 2.1, MISP e Sigma.

| Opção | Padrão | Significado |
|---|---|---|
| `ARQUIVO` | obrigatório | texto da isca; `-` lê da entrada padrão |
| `--case ID` | `CASE` | identificador do caso (entra nos IDs dos arquivos exportados) |
| `--tlp COR` | `AMBER` | `WHITE`/`CLEAR`, `GREEN`, `AMBER` ou `RED` (marcação TLP) |
| `--out DIR` | *(não exporta)* | pasta de saída; é criada se não existir |

O texto é "refangado" antes da análise: `hxxps://x[.]com` é lido como `https://x.com`.

### Exemplo

```bash
tropeiro lure examples/lure_receita.txt --case CASO-001 --tlp AMBER --out saida/
```

Entrada (`examples/lure_receita.txt`):

```text
Receita Federal: seu CPF está irregular. Regularize hoje em hxxps://receita-regulariza[.]example/cpf ou fale com o atendimento https://wa.me/5511999990000. Não perca o prazo. Banco Aurora S.A.
```

Saída:

```json
{
  "lures": [
    {"brand": "Receita Federal", "theme": "regularização CPF", "matched": ["receita federal"]}
  ],
  "iocs": {
    "url": ["https://receita-regulariza.example/cpf", "https://wa.me/5511999990000"],
    "phone": ["5511999990000"],
    "domain": ["receita-regulariza.example", "wa.me"],
    "whatsapp": ["5511999990000"]
  },
  "somente_contexto": {
    "url": ["https://wa.me/5511999990000"],
    "domain": ["wa.me"]
  }
}
defanged: receita-regulariza[.]example
exportado em saida/
```

Leitura:

- `lures`: a marca/tema reconhecido. Lista vazia = nenhuma regra conhecida bateu (não significa que seja legítima).
- `iocs`: tudo que foi extraído.
- `somente_contexto`: IOCs em **plataformas legítimas** (aqui, WhatsApp). Ficam no relatório mas **não** viram regra de bloqueio: bloquear `wa.me` quebraria o WhatsApp para todos. O número de telefone, esse sim, é o IOC.
- `defanged`: os domínios acionáveis já defangados, prontos para colar em um relatório ou e-mail.

### Arquivos gerados em `--out`

| Arquivo | Conteúdo |
|---|---|
| `stix.json` | pacote STIX 2.1 com `Campaign`, `Indicator`, observáveis e relações |
| `misp.json` | evento MISP com tags `tlp:*` e `type:phishing` |
| `sigma_dns.yml` | regra Sigma de consulta DNS (só se houver domínio acionável) |
| `sigma_network.yml` | regra Sigma de conexão a IP (só se houver IP) |

Detalhes de cada formato: [OUTPUTS](OUTPUTS.md).

### Pela entrada padrão

```bash
pbpaste | tropeiro lure - --case C2          # macOS
xclip -o | tropeiro lure - --case C2         # Linux
```

### Em scripts e CI

A CLI termina com código `0` quando conclui; erro de uso (opção inválida) e arquivo inexistente terminam com código diferente de zero. Para usar a saída JSON em outra ferramenta, a primeira parte (até a linha `defanged:`) é JSON; para uso programático prefira a [API Python](PYTHON_API.md), que devolve estruturas diretamente.

## `tropeiro workbench`

Abre o [Workbench](USER_GUIDE.md) no navegador local e bloqueia até `Ctrl+C`.

| Opção | Padrão | Significado |
|---|---|---|
| `--port N` | `7860` | porta local |
| `--share` | desligado | cria link público temporário do Gradio. **Não use com dados de casos reais** |

Escuta apenas em `127.0.0.1`.

## Limitações da CLI

- Não coleta nada da rede (DNS, RDAP, certificados...). Use o Workbench ou o notebook para isso.
- Usa só regras; para entidades de contexto (organização, registrar) com GLiNER use a [API Python](PYTHON_API.md#extração-híbrida) ou o Workbench.
- Regras de marca: lista curta e editável ([CONFIGURATION](CONFIGURATION.md#regras-de-iscas-brasileiras)).

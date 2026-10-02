# Tipos de busca

O Assistente Guiado muda o nome do campo de entrada conforme o tipo selecionado.

| Tipo | Exemplo | O que o Tropeiro faz |
|---|---|---|
| Domínio | `exemplo.com` | fluxo completo de domínio: DNS, RDAP, CT, histórico, scans públicos, lookalikes e correlação |
| URL | `https://exemplo.com/login` | extrai domínio e prioriza evidência web/redirects |
| IP | `203.0.113.10` | preserva como IOC de infraestrutura e evita módulos exclusivamente de domínio quando não aplicáveis |
| E-mail | `contato@exemplo.com` | usa como IOC/correlação defensiva; não busca dados privados do dono |
| Hash | SHA256/SHA1/MD5 | preserva para correlação e providers de threat intelligence compatíveis |
| Telefone | número já observado no caso | usa como IOC/correlação; não é reverse lookup de pessoa |
| Vários IOCs | um por linha | separa os tipos automaticamente |
| Texto da isca | mensagem recebida | extrai IOCs, marca/tema, CPF/CNPJ válidos, PIX e WhatsApp; separa plataformas legítimas; alimenta victimology e objetivo |

## Detectar automaticamente

Se você deixar **Detectar automaticamente**, o Tropeiro tenta reconhecer o tipo pelo formato.

Se a detecção ficar errada, escolha manualmente o tipo no dropdown.

## Busca por marca

Se estiver investigando impersonação:

- Alvo: domínio suspeito ou domínio oficial de referência;
- Marca: nome da marca;
- Organização imitada: opcional.

Preencher a marca melhora o contexto de lookalikes e análise de campanha.

## Múltiplos IOCs

Cole um por linha:

```text
dominio1.com
https://dominio2.com/login
203.0.113.10
hash...
```

O pipeline mantém cada tipo separado no inventário.

## Privacidade

E-mails e telefones devem ser indicadores já presentes numa investigação defensiva. O projeto não foi desenhado para encontrar endereço, identidade real ou outros dados privados de uma pessoa.

## Texto da isca: o que é extraído

Cole a mensagem inteira (aceita defang `hxxps://x[.]com`). O Tropeiro extrai:

| Item | Observação |
|---|---|
| domínios, URLs, IPs, e-mails, hashes | com validação de formato |
| telefones | normalizados (10 a 13 dígitos) |
| **CPF e CNPJ** | só se o **dígito verificador** estiver correto |
| **chave PIX aleatória** e **PIX copia-e-cola** | padrão do Banco Central |
| **WhatsApp** | `wa.me/<número>` e `api.whatsapp.com/send?phone=<número>` |
| **marca e tema** | Receita Federal, Correios, PIX, Detran/CNH, banco, INSS/Gov.br (regras editáveis) |
| entidades de contexto | organização, registrar... com GLiNER (opcional) |

Domínios e URLs de **plataformas legítimas** (WhatsApp, Telegram, Google...) ficam como contexto e não viram regra de bloqueio. Veja [INTERPRETING_RESULTS](INTERPRETING_RESULTS.md#plataformas-legítimas).

# Tipos de busca

O tipo do alvo decide **quais fontes são consultadas**. Com **AUTO**, o Tropeiro detecta o tipo pelo conteúdo; se errar, escolha o tipo manualmente.

## O que cada tipo consulta

| Tipo | Exemplo | Fontes consultadas |
|---|---|---|
| **Domínio** | `exemplo.com` | DNS (A, AAAA, CNAME, MX, NS), RDAP (registrar e **datas de registro**), crt.sh (certificados), urlscan (+ detalhes e identificadores duráveis), OTX, Wayback. Com `SAFE_ENRICHMENT`: Common Crawl. Com chave: VirusTotal, ThreatFox |
| **URL** | `https://exemplo.com/login` | as mesmas do domínio (host da URL). O caminho completo não é consultado, só o domínio |
| **IP** | `8.8.4.4` | DNS reverso (**PTR**), RDAP da rede (nome, país, organização, faixa), **scans do urlscan que viram o IP e os outros domínios hospedados nele**. Com chave: VirusTotal, ThreatFox |
| **E-mail** | `contato@exemplo.com` | coleta o **domínio** do e-mail (como no tipo Domínio). O endereço fica no caso como IOC; **nenhuma busca da pessoa ou da caixa** |
| **Hash** | SHA-256, SHA-1 ou MD5 | VirusTotal e ThreatFox, **só com chave**. Sem chave, nada é consultado e a tela diz qual variável definir |
| **Telefone** | `+55 31 99999-9999` | **nenhuma fonte pública**, por privacidade. Entra no caso para correlação e para a Campaign Memory |
| **Vários IOCs** | um por linha, ou separados por vírgula/`;` | cada item segue a regra do seu tipo |
| **Texto da isca** | a mensagem recebida | extrai entidades (regras brasileiras + GLiNER opcional), consulta **os domínios, IPs e hashes encontrados** (exceto plataformas legítimas), reconhece marca/tema e compara com iscas de casos anteriores |

IPs **privados, de loopback e de faixas de documentação** (`10.x`, `127.x`, `203.0.113.x`) não são consultados: não há o que perguntar à internet. Domínios de **plataformas legítimas** (WhatsApp, Google, Telegram, gov.br...) ficam como contexto e também não são consultados.

## Como o tipo é detectado

Regra central: **um texto com palavras é uma isca**, mesmo que contenha números e links. Só vira tipo simples o que é, por inteiro, um ou mais tokens daquele tipo.

| Entrada | Tipo detectado |
|---|---|
| `example[.]com`, `hxxps://x[.]com/a` | Domínio, URL (o defang é desfeito) |
| `example.com`, uma linha por IOC | Domínio |
| `example.com, 1.1.1.1` | Vários IOCs |
| `+55 11 99999-0000`, `11999990000` | Telefone |
| `Receita Federal: regularize em hxxps://x[.]com ou https://wa.me/5511999990000` | **Texto da isca** (e **não** telefone, apesar dos 13 dígitos) |
| `asdf qwerty` | Texto da isca |

> Antes da 4.8, um texto com um número de telefone era classificado como **Telefone** e nenhuma fonte rodava. Foi corrigido: veja [COMMON_ERRORS](COMMON_ERRORS.md).

## Busca por marca

Se estiver investigando impersonação, informe a **Marca** (e, opcionalmente, a organização imitada) nas opções avançadas. Ela melhora o contexto da análise.

## Vários IOCs

```text
dominio1.com
https://dominio2.com/login
8.8.4.4
d41d8cd98f00b204e9800998ecf8427e
```

Cada tipo é coletado separadamente; domínios criados em sequência no mesmo registrar aparecem na aba **Campanha**.

## Privacidade

E-mails e telefones devem ser indicadores já presentes numa investigação defensiva. O projeto não foi desenhado para encontrar endereço, identidade real ou outros dados privados de uma pessoa.

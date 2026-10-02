# Receitas

Sete fluxos completos, do começo ao fim. Valores de exemplo usam domínios `.example` e o IP de documentação `203.0.113.17`.

| # | Receita | Ferramenta |
|---|---|---|
| 1 | [Triagem de um domínio suspeito](#1-triagem-de-um-domínio-suspeito) | Workbench |
| 2 | [Analisar o texto de uma isca recebida](#2-analisar-o-texto-de-uma-isca-recebida) | CLI ou Workbench |
| 3 | [Processar vários IOCs de uma vez](#3-processar-vários-iocs-de-uma-vez) | Workbench |
| 4 | [Descobrir se já vi essa campanha](#4-descobrir-se-já-vi-essa-campanha) | Workbench + Campaign Memory |
| 5 | [Gerar regras de detecção e IOC para o TIP](#5-gerar-regras-de-detecção-e-ioc-para-o-tip) | CLI |
| 6 | [Preparar um pedido de takedown](#6-preparar-um-pedido-de-takedown) | Workbench |
| 7 | [Automatizar uma pasta de iscas](#7-automatizar-uma-pasta-de-iscas) | Python |

---

## 1. Triagem de um domínio suspeito

**Objetivo:** decidir em minutos se um domínio merece bloqueio, caça ou apenas monitoramento.

1. `tropeiro workbench`
2. **Tipo de busca:** `DOMAIN` (ou `AUTO`). **Alvo:** `dominio-suspeito.example`. **IA:** `OFF`.
3. Clique em **Executar investigação**.
4. Aba **Dados → Saúde das fontes**: confirme que DNS, RDAP e crt.sh estão `OK`. Se estiverem `UNAVAILABLE`, o resto não vale.
5. Aba **Dados → Evidence Ledger**: veja o IP resolvido, o registrar, as datas de registro (`rdap:created`; domínio criado há dias é sinal forte), atualização e expiração e os nomes de certificado.
6. Aba **IOCs**: leia a `decisão`.

**Interpretação**

| Você viu | Faça |
|---|---|
| `MONITOR` / `INSUFFICIENT_EVIDENCE` | não bloqueie; reavalie em 24 h (`revalidar`) |
| `HUNT` | procure o domínio e o IP nos seus logs DNS/proxy dos últimos 30 dias |
| `BLOCK` | bloqueie, registre a evidência e agende a revalidação |
| risco de FP `HIGH` | valide manualmente antes de qualquer bloqueio |

No Workbench rápido o resultado costuma ficar em `MONITOR`/`HUNT`: ele reúne evidência básica. Para a investigação completa (Wayback, VirusTotal, lookalikes) use o [notebook](COLAB.md).

---

## 2. Analisar o texto de uma isca recebida

**Objetivo:** transformar uma mensagem de SMS/WhatsApp/e-mail em IOCs e saber qual marca ela imita.

```bash
tropeiro lure isca.txt --case SMS-2026-017 --out saida/
```

(ou cole o texto no Workbench com **Tipo de busca = `LURE_TEXT`**).

Você recebe: marca e tema (`Receita Federal · regularização CPF`), domínios, URLs, telefone, WhatsApp, chave PIX, CPF/CNPJ válidos, e os arquivos STIX/MISP/Sigma. Veja o formato da saída em [CLI](CLI.md#exemplo).

**Dicas**

- Pode colar a mensagem **defangada** (`hxxps://x[.]com`).
- Não tire o link do texto original: o contexto ajuda a reconhecer a marca.
- Se `lures` vier vazio, nenhuma regra bateu: **não** conclua que a mensagem é legítima. Acrescente a marca às suas [regras](CONFIGURATION.md#regras-de-iscas-brasileiras).
- IOCs em `somente_contexto` (WhatsApp, Google...) **não** devem ser bloqueados por domínio.

---

## 3. Processar vários IOCs de uma vez

1. Workbench → **Tipo de busca = `MULTI_IOC`**.
2. Cole um por linha:

```text
dominio1.example
https://dominio2.example/login
203.0.113.17
```

3. Execute. Cada tipo é mantido separado no inventário, e os domínios são coletados individualmente.

Com **mais de 10 alvos** os limites de lookalikes e detalhes de scans caem automaticamente ([CONFIGURATION](CONFIGURATION.md#profundidade-provider_budget)). Para lotes grandes, ligue o cache (`http.set_cache`) e aumente `http.MIN_INTERVAL` para ser gentil com as fontes.

---

## 4. Descobrir se já vi essa campanha

**Objetivo:** ligar um caso novo a casos anteriores sem depender de IOC idêntico.

1. Deixe **Usar Campaign Memory** marcado (em *Opções avançadas*). Cada caso executado é guardado em `~/.tropeiro/tropeiro_case_memory.sqlite`.
2. Rode os casos normalmente. Se estiver no Colab, aponte a memória para o Drive (veja [CONFIGURATION](CONFIGURATION.md#campaign-memory)), ou ela some com o runtime.
3. No caso novo, abra a aba **Memória**:
   - **Casos relacionados:** os mais parecidos, com o que compartilham.
   - **Prevalência/raridade:** o que é comum (peso baixo) e o que é raro (peso alto).
4. Para uma isca sem IOC em comum, compare o texto: [`lure_similarity`](PYTHON_API.md#correlação-com-o-caso).

**Leitura**

- Compartilhar **um IP de hospedagem comum** quase não significa nada.
- Compartilhar **identificador raro, registrante específico ou o mesmo kit** é indício forte de mesma campanha.
- Nunca é "mesmo operador" automático (`same_operator_inferred = false`).

---

## 5. Gerar regras de detecção e IOC para o TIP

**Objetivo:** levar o que você aprendeu para o SIEM e a plataforma de inteligência.

```bash
tropeiro lure isca.txt --case CASO-001 --tlp AMBER --out saida/
```

| Para | Use | Como |
|---|---|---|
| MISP | `saida/misp.json` | importar como evento; só domínio/URL/IP/hash vão com `to_ids=true` |
| OpenCTI / outro TIP STIX | `saida/stix.json` | importar o pacote; `Indicator` com validade de 90 dias |
| SIEM | `saida/sigma_dns.yml` | `sigma convert -t <seu-siem> sigma_dns.yml` |

**Antes de ativar no SIEM:** rode a regra em modo de **alerta, não bloqueio**, por alguns dias; confira falsos positivos; o `valid_until` do STIX lembra que IOC de phishing envelhece rápido. Formatos em [OUTPUTS](OUTPUTS.md).

---

## 6. Preparar um pedido de takedown

**Objetivo:** reunir uma evidência que o registrar/hospedagem aceite e que você possa provar depois.

1. Execute o caso e confirme que o IOC está `TAKEDOWN_CANDIDATE` ou `BLOCK` (ativo, ≥ 2 famílias de fonte).
2. Em **Dados → Evidence Ledger**, anote o **registrar** (`rdap:registrar_org`), a **data de registro** (`rdap:created`) e o **IP** (`dns:A`). O provedor da hospedagem não é coletado: consulte o RDAP/WHOIS do IP.
3. No acordeão da aba **Exportar**, baixe o **ZIP** do caso. Ele traz `report.html`, o ledger, as decisões e o `manifest.json` (SHA-256).
4. Escreva o aviso ao contato de abuso do registrar e/ou da hospedagem (procure `abuse@` no RDAP/WHOIS do domínio e do IP).

Modelo de texto:

```text
Assunto: Phishing — pedido de suspensão de domínio

O domínio receita-regulariza[.]example (IP 203.0.113.17) hospeda uma página de phishing
que imita a Receita Federal e coleta CPF. Primeira observação: 2026-09-25 (UTC).
Evidências e hashes SHA-256 em anexo (pacote CASO-001). Solicitamos suspensão e
preservação dos registros.
```

**Cuidados**

- Use sempre o domínio defangado em e-mails.
- **Não** acesse a URL ao vivo pelo seu computador pessoal; use os scans públicos do urlscan já coletados.
- Guarde o ZIP e o `manifest.json`: provam o que você tinha e quando.
- O Tropeiro não executa takedown nem "toma" recursos; ele só prepara a evidência.

---

## 7. Automatizar uma pasta de iscas

**Objetivo:** analisar todas as mensagens de uma pasta e consolidar os IOCs, sem interface.

```python
from pathlib import Path
from tropeiro.intelligence.br_lures import detect_br_lures, extract_lure_infra
from tropeiro.intelligence.legit_domains import partition_iocs

consolidado = {}
for arquivo in sorted(Path("examples").glob("lure*.txt")):
    texto = arquivo.read_text(encoding="utf-8")
    acionaveis, _contexto = partition_iocs(extract_lure_infra(texto))
    marcas = [m["brand"] for m in detect_br_lures(texto)]
    for dominio in acionaveis.get("domain", []):
        consolidado.setdefault(dominio, set()).update(marcas)

assert "receita-regulariza.example" in consolidado
assert "Receita Federal" in consolidado["receita-regulariza.example"]
```

Para gerar os arquivos de exportação dentro do script, combine com `bundle_from_iocs`, `misp_event` e `sigma_rules` ([PYTHON_API](PYTHON_API.md#exportações)). Para rodar em CI, instale só o núcleo (`pip install -e .`): nada disso precisa de rede nem de modelos.

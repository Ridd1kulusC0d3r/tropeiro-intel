# API Python

Tudo que a CLI e o Workbench fazem está disponível como biblioteca. **Cada bloco `python` desta página é executado nos testes** (`tests/test_docs.py`), então os exemplos funcionam como estão, offline.

```bash
pip install -e .            # núcleo
```

## Extração híbrida

`extract_hybrid` combina regras determinísticas (sempre) e GLiNER (opcional). Funciona **sem modelo**.

```python
from tropeiro.ai import extract_hybrid

texto = open("examples/lure_receita.txt", encoding="utf-8").read()
entidades = extract_hybrid(texto)                 # só regras

dominio = next(e for e in entidades if e["type"] == "domain" and e["value"] == "receita-regulariza.example")
assert dominio["methods"] == ["rule"] and dominio["confidence"] == "HIGH"
assert dominio["derived"] and not dominio["analyst_confirmed"]     # candidato, não evidência
assert any(e["type"] == "brand" and e["value"] == "Receita Federal" for e in entidades)
assert any(e["type"] == "whatsapp" and e["value"] == "5511999990000" for e in entidades)
```

Cada entidade traz `type`, `value`, `methods` (`rule`, `gliner` ou ambos), `score`, `confidence` e, quando for o caso, `legit_platform`.

Com o GLiNER (precisa do extra `ai`):

```python
# from tropeiro.ai import GLiNERLocal
# entidades = extract_hybrid(texto, gliner=GLiNERLocal())    # rule+gliner concordando sobem de confiança
```

O texto é "refangado" antes (`hxxps://x[.]com` vira `https://x.com`), e saídas do modelo inválidas (domínio malformado, IP impossível) são descartadas:

```python
from tropeiro.utils import refang
assert refang("hxxps://exemplo[.]com") == "https://exemplo.com"
```

## Correlação com o caso

```python
from tropeiro.ai import extract_hybrid, correlate_entities

entidades = extract_hybrid("Acesse hxxps://pagamento[.]receita-regulariza[.]example")
conhecidos = ["receita-regulariza.example", "regulariza-cpf.example"]     # o que já foi coletado no caso
ligacoes = correlate_entities(entidades, conhecidos)

assert any(l["relation"] == "same_root_domain" and l["dst"] == "receita-regulariza.example" for l in ligacoes)
assert all(l["derived"] and not l["analyst_confirmed"] for l in ligacoes)
```

Relações: `same_value`, `same_root_domain`, `similar_name`. Para comparar iscas entre casos, mesmo sem IOC em comum:

```python
from tropeiro.ai import lure_similarity

parecidos = lure_similarity(
    "Sua conta precisa de validação, acesse o link para regularizar",
    {"CASO-A": "Sua conta precisa de validação! Acesse o link para regularizar", "CASO-B": "promoção de verão"},
)
assert [p["case_id"] for p in parecidos] == ["CASO-A"]
```

## Iscas brasileiras

```python
from tropeiro.intelligence.br_lures import detect_br_lures, extract_lure_infra, valid_cpf, valid_cnpj

texto = "Receita Federal: regularize seu CPF 529.982.247-25 em https://wa.me/5511999990000"
assert detect_br_lures(texto)[0]["brand"] == "Receita Federal"

infra = extract_lure_infra(texto)
assert infra["cpf"] == ["52998224725"] and infra["whatsapp"] == ["5511999990000"]

assert valid_cpf("529.982.247-25") and not valid_cpf("529.982.247-24")      # dígito verificador
assert valid_cnpj("11.222.333/0001-81") and not valid_cnpj("11.222.333/0001-82")
```

CPF/CNPJ sem dígito verificador correto são **ignorados** (evita confundir número qualquer com documento). Também extrai chave PIX aleatória (`pix_evp`) e PIX copia-e-cola (`pix_copia_cola`).

## Plataformas legítimas

```python
from tropeiro.intelligence.legit_domains import partition_iocs, is_known_legit

acionaveis, contexto = partition_iocs({
    "domain": ["receita-regulariza.example", "wa.me"],
    "url": ["https://wa.me/5511999990000", "https://docs.google.com/forms/d/abc"],
})
assert acionaveis["domain"] == ["receita-regulariza.example"] and contexto["domain"] == ["wa.me"]
assert contexto["url"] == ["https://wa.me/5511999990000"]                   # app de mensagem: o IOC é o número
assert acionaveis["url"] == ["https://docs.google.com/forms/d/abc"]         # URL específica segue acionável
assert is_known_legit("docs.google.com") and not is_known_legit("google.com.evil.example")
```

## Decisão por IOC

```python
from tropeiro.intelligence.decision_objects import build_ioc_decisions
from tropeiro.intelligence.warninglists import WarningListEngine

candidatos = [{
    "value": "receita-regulariza.example", "type": "domain", "confidence": 0.85, "active": True,
    "evidence_count": 9, "source_families": 4, "campaign": "CASO-001", "context": {}, "rationale": ["exemplo"],
}]
d = build_ioc_decisions(candidatos, WarningListEngine())[0]
assert d["decision"] == "BLOCK" and d["confidence_band"] == "HIGH"

# mesma evidência, mas uma só família de fonte: o Tropeiro não recomenda bloqueio
candidatos[0]["source_families"] = 1
assert build_ioc_decisions(candidatos, WarningListEngine())[0]["decision"] != "BLOCK"
```

## Exportações

```python
import json
from tropeiro.reporting.stix import bundle_from_iocs, validate
from tropeiro.reporting.misp import misp_event
from tropeiro.intelligence.sigma import sigma_rules

iocs = {"domain": ["receita-regulariza.example"], "ip": ["203.0.113.17"]}
contexto = {"domain": ["wa.me"]}                       # plataformas legítimas: só observáveis, nunca Indicator

stix = bundle_from_iocs(iocs, case_id="CASO-001", tlp="AMBER", confidence=70, context_only=contexto)
parsed = validate(stix.serialize())                    # re-lê e valida com a biblioteca stix2
tipos = [o["type"] for o in parsed.objects]
assert tipos.count("indicator") == 2 and "campaign" in tipos

evento = misp_event("CASO-001", iocs, tlp="AMBER", context_only=contexto)["Event"]
por_valor = {a["value"]: a["to_ids"] for a in evento["Attribute"]}
assert por_valor == {"receita-regulariza.example": True, "203.0.113.17": True, "wa.me": False}

regras = sigma_rules(iocs, "CASO-001")
assert set(regras) == {"dns", "network"} and "selection or selection_sub" in regras["dns"]
```

`tlp` aceita `WHITE`, `CLEAR`, `GREEN`, `AMBER`, `RED`. Reexportar o mesmo caso gera os **mesmos IDs** STIX.

## Validação de alvo

```python
from tropeiro.utils import valid_hostname

assert valid_hostname("Exemplo.COM.") == "exemplo.com"
assert valid_hostname("bücher.de") == "xn--bcher-kva.de"
assert valid_hostname("a.com/../x") is None and valid_hostname("a.com?x=1") is None
```

## Kit de phishing e lotes de registro

```python
from tropeiro.similarity.kit import kit_fingerprint, kit_similarity, cluster_kits
from tropeiro.correlation.registration import registration_batches

kit_a = {"index.html": b"x", "js/app.js": b"y", "img/logo.png": b"z"}
kit_b = {**kit_a, "extra.txt": b"q"}                   # mesmo kit com um arquivo a mais
assert kit_similarity(kit_a, kit_b) == 0.75
assert cluster_kits({"d1.example": kit_a, "d2.example": kit_b, "d3.example": {"outro.html": b"1"}}) == [["d1.example", "d2.example"]]
assert kit_fingerprint(kit_a) == kit_fingerprint(dict(reversed(list(kit_a.items()))))      # independe da ordem

linhas = [{"domain": f"d{i}.example", "created": f"2026-03-01T10:00:{i*10:02d}Z", "registrar": "R", "nameservers": ["ns1.x"]} for i in range(3)]
lotes = registration_batches(linhas, window_seconds=600)
assert lotes[0]["domains"] == ["d0.example", "d1.example", "d2.example"] and "reason" in lotes[0]
```

São **indícios** de operação comum, não prova: o motivo vem junto para o analista julgar.

## Linha do tempo

```python
from tropeiro.timeline import timeline_summary, timeline_markdown

eventos = [
    {"entity": "a.example", "observed_at": "2026-01-02", "source": "crtsh"},
    {"entity": "a.example", "observed_at": "2026-01-01", "source": "rdap"},
]
resumo = timeline_summary(eventos)["a.example"]
assert resumo["first_seen"] == "2026-01-01" and resumo["sources"] == ["crtsh", "rdap"]
assert "`a.example`" in timeline_markdown(eventos)
```

## Calibração de confiança

Compare o score do Tropeiro com o veredito humano de casos passados (`1` = campanha confirmada).

```python
from tropeiro.intelligence.calibration import calibration_report

casos = [(0.9, 1), (0.8, 1), (0.2, 0), (0.1, 0), (0.7, 0)]
r = calibration_report(casos)
assert r["cases"] == 5 and r["brier"] < 0.25 and r["reliability"]
```

`brier` menor é melhor (0,25 equivale a chutar 50%). `reliability` mostra, por faixa de score, a taxa real de acerto.

## Campaign Memory

```python
import tempfile
from pathlib import Path
from tropeiro.memory import CaseMemory
from tropeiro.reporting.context import build_report_data

with tempfile.TemporaryDirectory() as td:
    dados = build_report_data({"CASE_ID": "CASO-1", "WORKSPACE": Path(td), "ENABLE_DNS": True}, version="doc")
    memoria = CaseMemory(Path(td) / "memoria.sqlite")
    memoria.store_case(dados)
    assert memoria.stats()["cases"] == 1
```

`memoria.compare_report(dados, exclude_case_id=...)` devolve os casos parecidos; `prevalence_for_report` devolve a raridade de cada artefato. Veja [CAMPAIGN_MEMORY](CAMPAIGN_MEMORY.md).

## Rede: cache, limite e retry

```python
from tropeiro import http

http.MIN_INTERVAL = 2.0                    # segundos entre chamadas ao mesmo host
http.set_cache(None)                       # desliga o cache (use um caminho para ligar)
assert http.RETRY_STATUS == {429, 500, 502, 503, 504}
```

## Resposta do Qwen: verificação

`run_qwen_analysis` aceita qualquer objeto com método `chat(system, user, max_new_tokens)`. Isto permite testar sem modelo:

```python
from tropeiro.ai import run_qwen_analysis

class FalsoChat:
    def __init__(self, respostas): self.respostas = list(respostas)
    def chat(self, system, user, max_new_tokens=0): return self.respostas.pop(0)

pacote = {"schema": "x", "evidence_ledger": [{"evidence_id": "EV-1"}], "packet_sha256": "h"}
resposta = ('{"executive_summary":"s","key_findings":['
            '{"statement":"a","analytic_type":"observed","confidence":"HIGH","evidence_refs":["EV-404"]},'
            '{"statement":"b","analytic_type":"observed","confidence":"HIGH","evidence_refs":["EV-1"]}]}')
saida = run_qwen_analysis(FalsoChat(["não é JSON", resposta]), pacote)

assert saida["_generation_status"] == "OK_RETRY"                       # 1 nova tentativa pedindo só JSON
a, b = saida["key_findings"]
assert a["analytic_type"] == "hypothesis" and a["confidence"] == "INSUFFICIENT"      # EV-404 não existe: rebaixado
assert b["analytic_type"] == "observed"                                              # EV-1 existe: mantido
```

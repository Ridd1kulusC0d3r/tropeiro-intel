# Tropeiro Intel

> **Campaign Intelligence for phishing investigations, built for analysts and designed to run in Google Colab.**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)
[![CI](https://github.com/Ridd1kulusC0d3r/tropeiro-intel/actions/workflows/ci.yml/badge.svg)](https://github.com/Ridd1kulusC0d3r/tropeiro-intel/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-black.svg)](https://www.python.org/)

**Tropeiro Intel** is a defensive OSINT / threat-intelligence laboratory for investigating phishing and fraud campaigns from domains, URLs, IPs, hashes, observed contacts and lure text.

```text
COLLECT → NORMALIZE → EVIDENCE → CORRELATE → ASSESS → ATTRIBUTE → DECIDE → PIVOT → REPORT
```

## Primeira vez usando Colab ou OSINT?

Comece pelo **[Guia para iniciantes](docs/BEGINNER_GUIDE.md)**.

A **4.1 Guided Investigation Station** inclui um assistente que muda o campo de entrada conforme o caso:

```text
Domínio
URL
IP
E-mail observado
Hash
Telefone observado
Vários IOCs
Texto da isca
```

Também há uma caixa **🧭 Antes de executar** imediatamente antes de cada etapa do notebook explicando objetivo, como usar, saída esperada, erros mais comuns e o que fazer quando algo falhar.

Material essencial:

- [Guia para iniciantes](docs/BEGINNER_GUIDE.md)
- [Tipos de busca](docs/SEARCH_TYPES.md)
- [Erros comuns](docs/COMMON_ERRORS.md)
- [Glossário](docs/GLOSSARY.md)

## Start here

### ▶ [Open Tropeiro Intel in Google Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)

No paid API is required for the core workflow.

For a first investigation:

1. run **01 · Bootstrap**;
2. run **02 · Health Check**;
3. configure the target in **04 · Assistente guiado**;
4. keep **PASSIVE**;
5. keep **Usar plano automático recomendado** in step 05;
6. continue in order.

## Simple Colab frontend

After bootstrap, the notebook can launch a **Gradio Investigation Workbench inside Colab**. It provides target input, mode/budget controls, optional GLiNER/Qwen, source health, IOC/evidence/relationship tables and report/package downloads.

The frontend is a convenience layer over the same `tropeiro/` backend. The full notebook remains available for advanced analysis.

## Guided investigation

The visible input changes according to the selected or detected IOC type. Internally the guided layer still populates the stable backend objects and variables, preserving advanced workflows.

The automatic scan plan considers:

- effective input type;
- PASSIVE / SAFE_ENRICHMENT / AUTHORIZED_ACTIVE;
- provider budget;
- configured secrets;
- brand context;
- number of targets.

Advanced analysts can disable automatic planning and manually control every feature.

## What Tropeiro answers

- What is related to this IOC?
- Which relationships are actually discriminating?
- Which infrastructure is shared, reused or merely coincidental?
- Which domains appear to belong to the same campaign?
- Is there evidence for a common operator, or only a shared kit/provider?
- What is still unknown?
- Which pivot is worth pursuing next?
- Which IOCs are suitable for **BLOCK, HUNT, MONITOR or TAKEDOWN PREP**?
- How strong is the attribution, and what alternative hypotheses remain?

## Core capabilities

| Capability | Status | Purpose |
|---|---|---|
| Guided IOC input | ✅ | dynamic DOMAIN / URL / IP / EMAIL / HASH / PHONE / MULTI / LURE input |
| Automatic scan plan | ✅ | recommends modules from case context |
| Multi-IOC ingestion | ✅ | normalizes mixed indicators |
| Passive DNS / RDAP / CT | ✅ | registration and infrastructure evidence |
| Wayback / Common Crawl | ✅ | historical web context |
| urlscan / OTX | ✅ | passive enrichment and scan history |
| VirusTotal / ThreatFox | Optional | threat-intelligence enrichment |
| dnstwist | ✅ | lookalike candidate generation |
| Domain similarity | ✅ | lexical/token/confusable comparison |
| Evidence Ledger | ✅ | provenance and source reliability |
| Source independence | ✅ | prevents derived feeds from inflating confidence |
| Relationship graph | ✅ | typed entity relationships |
| Guarded clustering | ✅ | reduces cluster explosion on shared infrastructure |
| Campaign / operator fingerprints | ✅ | separate operational representations |
| Attribution / ACH | ✅ | competing hypotheses and attribution ladder |
| PIRs / collection gaps | ✅ | unanswered intelligence requirements |
| Next Best Pivot | ✅ | ranks useful next collection steps |
| IOC Decision Objects | ✅ | actionability and FP control |
| Detection bridge | ✅ | hunt/detection candidates |
| Local rich report | ✅ | offline HTML + selective export |
| DNSDumpster / FOFA / Censys | Optional | deeper enrichment |

## Analytical guardrails

```text
Infrastructure ownership ≠ campaign membership
Campaign membership       ≠ common operator
Common operator           ≠ real-world identity
Real-world identity       ≠ known threat actor
```

Shared IPs, ASNs, registrars, CDNs and hosting providers are not sufficient attribution.

## API keys and secrets

Optional secrets can be configured in the Colab key icon:

```text
URLSCAN_API_KEY
VT_API_KEY
THREATFOX_AUTH_KEY
DNSDUMPSTER_API_KEY
FOFA_API_KEY
CENSYS_PAT
CENSYS_ORG_ID
```

Do not paste API keys into public notebook cells.

## Documentation

- [Beginner guide](docs/BEGINNER_GUIDE.md)
- [Search types](docs/SEARCH_TYPES.md)
- [Common errors](docs/COMMON_ERRORS.md)
- [Glossary](docs/GLOSSARY.md)
- [Quick start](docs/QUICKSTART.md)
- [Official Colab guide](docs/COLAB.md)
- [Intelligence model](docs/INTELLIGENCE_MODEL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Attribution engineering](docs/ATTRIBUTION.md)
- [Data model](docs/DATA_MODEL.md)
- [Actionable intelligence](docs/ACTIONABLE_INTELLIGENCE.md)
- [Reporting UX](docs/REPORTING_UX.md)
- [Security and safe use](SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Feature validation matrix](docs/FEATURE_MATRIX.md)

## Local Python usage

```bash
git clone https://github.com/Ridd1kulusC0d3r/tropeiro-intel.git
cd tropeiro-intel
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,colab]"
pytest -q
```

## Safety model

- Passive by default.
- Direct HTTP probing is opt-in and requires authorization.
- No resource claiming or takeover exploitation.
- No private-PII hunting or doxxing workflows.
- Observed e-mails/phones are correlation indicators, not invitations to search for private owners.
- Attribution is evidence-backed confidence, not accusation.

## Project status

Current public release: **4.1 Guided Investigation Station**.

## License

Apache-2.0. See [LICENSE](LICENSE).

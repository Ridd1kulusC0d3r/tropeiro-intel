# Tropeiro Intel

> **Campaign Intelligence for phishing investigations, built for analysts and designed to run in Google Colab.**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)
[![CI](https://github.com/Ridd1kulusC0d3r/tropeiro-intel/actions/workflows/ci.yml/badge.svg)](https://github.com/Ridd1kulusC0d3r/tropeiro-intel/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-black.svg)](https://www.python.org/)

**Tropeiro Intel** is a defensive OSINT / threat-intelligence laboratory for investigating phishing and fraud campaigns from domains, URLs, IOCs and lure text. Its goal is not to produce a pile of API responses. It turns observations into **evidence, relationships, assessments, actions and next collection priorities**.

```text
COLLECT → NORMALIZE → EVIDENCE → CORRELATE → ASSESS → ATTRIBUTE → DECIDE → PIVOT → REPORT
```

## Start here

The official experience is the Colab notebook:

### ▶ [Open Tropeiro Intel in Google Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)

No paid API is required for the core workflow. Optional providers deepen coverage when credentials are available.

## What Tropeiro answers

Instead of stopping at “is this domain suspicious?”, the workflow is designed to help answer:

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
| Multi-IOC ingestion | ✅ | domains, URLs, IPs, e-mails, phones, hashes and lure text |
| Passive DNS / RDAP / CT | ✅ | registration and infrastructure evidence |
| Wayback / Common Crawl | ✅ | historical web context |
| urlscan / OTX | ✅ | passive enrichment and scan history |
| VirusTotal / ThreatFox | Optional | threat-intelligence enrichment |
| dnstwist | ✅ | lookalike candidate generation |
| Evidence Ledger | ✅ | provenance and source reliability |
| Campaign graph | ✅ | typed entity relationships |
| Campaign clustering | ✅ | campaign-level grouping |
| Campaign fingerprint | ✅ | reusable campaign traits |
| Ownership plane | ✅ | registrar / registrant org / ASN / certificates |
| Operator correlation | ✅ | evidence-weighted relationship assessment |
| Competing hypotheses | ✅ | same operator vs shared kit/hosting/reseller/coincidence |
| Attribution ladder | ✅ | prevents correlation from becoming identity by magic |
| PIRs / collection gaps | ✅ | investigation requirements and unanswered questions |
| Next Best Pivot | ✅ | ranks the next collection step |
| IOC Decision Objects | ✅ | actionability, FP risk and operational action |
| Detection bridge | ✅ | hunt/detection candidates |
| Local rich report | ✅ | offline HTML cockpit + selective export |
| STIX 2.1 / MISP-like export | ✅ | interoperability |
| DNSDumpster / FOFA / Censys | Optional | deeper infrastructure enrichment |

## Analytical guardrails

```text
Infrastructure ownership ≠ campaign membership
Campaign membership       ≠ common operator
Common operator           ≠ real-world identity
Real-world identity       ≠ known threat actor
```

A shared IP, ASN, registrar, hosting company or CDN is **not** sufficient attribution. High-confidence conclusions require multiple independent, discriminating signals.

## Colab quick start

1. Open the official notebook.
2. Run **Installation**.
3. Set `CASE_ID`, seeds and optional lure text.
4. Keep `ENABLE_HTTP_PROBE = False` unless you are working on an authorized target.
5. Add optional API credentials through **Colab Secrets** or environment variables.
6. Run the notebook top-to-bottom.
7. Review **Executive Assessment**, **Action Matrix**, **IOC Decisions**, **Attribution**, **Collection Gaps** and **Next Best Pivots**.
8. Generate the local enriched HTML report.
9. Export only the artifacts required for the audience.

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the full walkthrough.

## API keys and secrets

The notebook works without paid providers. When keys are available, prefer Colab Secrets with these names:

```text
URLSCAN_API_KEY
VT_API_KEY
THREATFOX_AUTH_KEY
DNSDUMPSTER_API_KEY
FOFA_API_KEY
CENSYS_PAT
CENSYS_ORG_ID
```

Keys are not required to be committed, pasted into the repository or included in reports. Humanity has already leaked enough credentials into Git history.

## Output model

```text
Executive Brief
Action Matrix
IOC Decision Objects
Campaign Clusters
Ownership Summary
Operator Correlation
Attribution Assessment
Collection Gaps
Next Best Pivots
Detection Package
Evidence Ledger
Timeline
STIX 2.1
MISP-like Event
Local HTML Report
```

## Documentation

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

## Local Python usage

```bash
git clone https://github.com/Ridd1kulusC0d3r/tropeiro-intel.git
cd tropeiro-intel
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e ".[dev,colab]"
pytest -q
```

## Safety model

- Passive by default.
- Direct HTTP probing is opt-in.
- No automatic exploitation or resource claiming.
- No private-PII hunting or doxxing workflows.
- Public contacts used for correlation should be minimized or hashed in reports.
- Attribution is expressed as evidence-backed confidence, not accusation.
- “No hit” in a threat feed never means “benign”.

## Project status

Current public release: **3.1.1 Public Preview**.

The current emphasis is analytical quality: better relationships, stronger provenance, lower false-positive risk and more defensible attribution. See the [roadmap](docs/ROADMAP.md) for the next correlation and historical-intelligence layers.

## License

Apache-2.0. See [LICENSE](LICENSE).

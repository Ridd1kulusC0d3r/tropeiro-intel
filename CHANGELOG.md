# Changelog

## 4.8.0 A search that actually runs
Reproduced a real search end to end (fresh install, real network, real browser and the full notebook) and fixed what blocked it.
- **Fix:** the Workbench showed no result and no error when its output files were outside the folders Gradio serves (`InvalidPathError`). Copies are now published to a servable folder and `allowed_paths` is set.
- **Fix:** the Colab Workbench (cell 06A) forced `share=False`; Gradio needs a public link in Colab and decides it itself when `share=None`.
- **Fix:** a pasted lure containing a phone number was classified as PHONE and no source ran. A text with words is now always a lure (`tropeiro.targets`).
- **Fix:** IP, e-mail, hash and phone searches queried nothing. IP now collects PTR, RDAP and urlscan (hosted domains); e-mail collects its domain; hash uses VirusTotal/ThreatFox (keys); phone explains why nothing is queried.
- **Perf:** sources run **concurrently** under a total deadline (45/90/180 s, `TIMEOUT` rows), per-call timeout cap (20 s), no retry storms (Wayback/Common Crawl: 1 attempt), urlscan detail circuit breaker, per-host intervals. A domain went from ~115 s (serial, 13 failures) to 10-35 s.
- **New:** `tropeiro search` (full search with live progress, exit code 2 when no source answers), `tropeiro doctor` (+ "Diagnóstico do ambiente" panel), `investigate()` / `plan_investigation()` / `run_tasks()` API, `TROPEIRO_WORKSPACE`, automatic free port for `tropeiro workbench`.
- **UI:** live per-source progress, visible error panel, states in Portuguese in "Saúde das fontes", short lure title, relation table columns in Portuguese.
- **Notebook:** guide cards no longer dump the cell code into the text (56 cards), target form fields (`ALVO`/`TIPO`) as a fallback when widgets do not render, 06A explains the public link. Full "Run all" executes with 0 errors in 65 s.
- **Refactor:** one pipeline (`pipeline.py`) shared by UI, CLI and API; `frontend/app.py` is now a thin layer; `enrich` moved to `enrichment.py`; `run_quick_case` kept as an alias.
- crt.sh: 2 attempts including transient 404/502/503. Docs rewritten to match (CLI, SEARCH_TYPES, CONFIGURATION, TROUBLESHOOTING, USER_GUIDE, PYTHON_API with runnable examples).

## 4.7.0 Phase 0: Workbench, notebook and models aligned
- Workbench now honours **mode and depth** (`recommended_features` / `budget_limits`): Wayback, Common Crawl (SAFE_ENRICHMENT), VirusTotal and ThreatFox (with keys), urlscan details with **durable identifiers** (GA/GTM/AdSense/pixel) capped by depth.
- New **Campanha** tab: registration batches (same registrar/NS, created in sequence) and similar lures from the Campaign Memory (`CaseMemory.lure_texts`; the text stays in the local DB, never in the exported case.json).
- HTTP cache enabled in the Workbench; hostname validation also in OTX, VirusTotal, Wayback and Common Crawl collectors.
- Notebook: refang on ingestion, new cell 08B (BR lures, legitimate platforms) and 55B (STIX 2.1 / MISP / Sigma export).
- Models validated for real on CPU (GLiNER + Qwen3-0.6B). Fix: the `ai` extra was incomplete (`sentencepiece`, `protobuf` added).
- CI: new `workbench` job runs the front-end tests on Gradio 5 and 6; tests block real network access (`tests/conftest.py`).
- Removed dead code `storage/case_store.py`.

## 4.6.1 Documentation overhaul and fixes
- Docs: new index, installation, configuration, Workbench user guide (with screenshots), CLI, outputs/formats, results interpretation, cookbook (7 recipes), Python API, FAQ; refreshed quickstart, glossary, common errors, search types, contributing. Python examples in `docs/` are executed in CI; relative links are checked.
- Fix: the CLI did not refang input, so defanged lure domains were lost. `extract_lure_infra` now refangs.
- Fix: legitimate platforms (WhatsApp, Telegram, Google, gov.br...) were exported as blocking IOCs. New `intelligence.legit_domains`; STIX/MISP/Sigma now carry them as context only (no Indicator, `to_ids=false`); the UI shows a "PLATAFORMA LEGÍTIMA" badge.
- Fix: Sigma DNS rule matched `endswith 'domain'` (also `notdomain`); now exact match or subdomain.
- Fix: Workbench now records `rdap:created/updated/expires` in the ledger; its ZIP includes STIX/MISP/Sigma and a manifest that hashes them.
- New: `tropeiro workbench` command and `launch_local()`.

## 4.6.0 Workbench v2, hybrid AI, project materials
- Front redesigned (dark theme, KPI cards, SVG relationship graph, curated IOC decision table, timeline, STIX/MISP/Sigma export tab, offline demo case). Fixed `KeyError` on `related_cases`/`artifact_prevalence` and a hard-coded `/content` workspace outside Colab.
- AI: `extract_hybrid` (refang + BR rules always on, GLiNER optional, model output validated, rule+model agreement boost), `correlate_entities`, `lure_similarity`; Qwen JSON retry and `enforce_evidence_support` (unsupported findings downgraded).
- Materials: logo, architecture diagram, social preview, demo GIF + screenshots (`scripts/make_demo_media.py`), README, AI/Workbench docs, CITATION, issue/PR templates, dependabot.

## 4.5.0 Hardening and exports
- `http`: retry only on 429/5xx/timeouts (honours `Retry-After`), per-host rate limit, optional disk cache (`http.set_cache`).
- `utils.valid_hostname` validates targets before they enter collector URLs (crt.sh, RDAP).
- STIX export now emits Indicators (validity window, TLP, confidence), a Campaign and Relationships, with deterministic IDs.
- MISP export: hash types by length, phone, TLP tags; `to_ids` only for domain/url/ip/hash by default.
- New: phishing-kit fingerprint (`similarity.kit`), registration batches (`correlation.registration`), BR lure rules with CPF/CNPJ check-digit validation, PIX/WhatsApp extraction (`intelligence.br_lures`), Sigma generator, confidence calibration (Brier/reliability), `timeline_summary`, offline CLI (`tropeiro lure`).
- CI: ruff (syntax/undefined-name subset).

## 4.4.1 Colab Widget Compatibility
- Fixed the guided case form using `IPython.display.HTML` inside `ipywidgets.VBox`, which raised `TraitError` on current Colab runtimes.
- The guided case form and scan-plan header now use `widgets.HTML`.
- Made the scan-plan cell self-contained for `ipywidgets`, `display`, `clear_output`, and `re`.
- Added Python 3.13 to CI and a runtime smoke test that executes the guided widget cells.

## 4.1.0 Guided Investigation Station
- Dynamic guided input for DOMAIN / URL / IP / EMAIL / HASH / PHONE / MULTI_IOC / LURE_TEXT.
- Input label and placeholder change according to investigation type.
- Automatic input-type detection with manual override.
- Automatic scan recommendations based on type, mode, budget, secrets and brand.
- All advanced feature flags remain available through manual override.
- Provider requirements are derived from the case rather than one fixed requirement list.
- Budget-aware dnstwist and urlscan limits.
- Instruction card before every executable notebook cell.
- Beginner guide, search-type guide, common-error handbook and glossary.
- Onboarding unit tests.

## 4.0.0 Investigation Station
- Restored the full investigation-station experience to the official Colab.
- Added PASSIVE / SAFE_ENRICHMENT / AUTHORIZED_ACTIVE modes.
- Added Provider Query Planner.
- Added domain similarity, durable identifiers, Source Independence, Cluster Explosion Guard, Negative Evidence and expanded reporting.

## 3.1.1 Public Preview
- Initial public GitHub/Colab release.

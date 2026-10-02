# Changelog

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

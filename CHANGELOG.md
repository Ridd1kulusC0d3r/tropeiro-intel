# Changelog

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

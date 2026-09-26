# Changelog

## 4.0.0 Investigation Station
- Restored the full investigation-station experience to the official Colab (75 cells).
- Added PASSIVE / SAFE_ENRICHMENT / AUTHORIZED_ACTIVE modes; incompatible HTTP probing no longer crashes the case setup.
- Added Provider Query Planner with budget/secret-aware SKIPPED states.
- Added domain similarity engine with Levenshtein, Jaro-Winkler, n-grams, token overlap and TLD/confusable signals.
- Added passive durable-identifier and web-fingerprint extraction from scan artifacts.
- Added Source Independence Engine, weighted relationship metadata and Cluster Explosion Guard.
- Added campaign and operator fingerprints as separate analytical objects.
- Added explicit Negative Evidence modeling.
- Expanded lifecycle to PREPARATION / STAGING / ACTIVE / EXPANSION / DECAY / DORMANT / REACTIVATED.
- Added conservative passive dangling-CNAME exposure detection without resource claiming/exploitation.
- Hardened IOC Decision Engine with source/evidence minimums and policy-controlled thresholds.
- Expanded detection candidates to Sigma, Splunk, Sentinel KQL, Elastic ES|QL, Wazuh and Suricata.
- Rebuilt the offline report backend with relationship graph, timeline, similarity, churn, source independence, provider plan and expanded exports.
- Added Feature Validation Matrix and advanced offline/unit tests.

## 3.1.1 Public Preview
- Initial public GitHub/Colab release.

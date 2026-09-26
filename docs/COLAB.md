# Official Investigation Station — Google Colab

The canonical machine is `notebooks/Tropeiro_Intel_Official_Colab.ipynb`.

It intentionally exposes the investigation as a long, inspectable workflow while keeping implementation logic in the `tropeiro/` package. In 4.0 the notebook contains **75 cells**, including section headers, so analysts can run, inspect, rerun and skip individual layers without editing backend code.

## Operating modes

- `PASSIVE` — default. Public/passive sources only.
- `SAFE_ENRICHMENT` — optional provider enrichment, still no direct target probing.
- `AUTHORIZED_ACTIVE` — enables explicitly opted-in low-impact direct checks only when the analyst has authorization.

Selecting an incompatible feature no longer intentionally crashes the notebook. It is disabled with a visible warning/status instead.

## Main investigation planes

1. Case setup / Secrets / Provider Planner
2. IOC ingestion and normalization
3. DNS / RDAP / CT / historical sources
4. urlscan / TI / optional infrastructure providers
5. dnstwist and Domain Similarity
6. Passive web fingerprints and durable identifiers
7. Evidence Ledger and Source Independence
8. Relationship Graph and guarded clustering
9. Campaign / Operator fingerprints
10. Timeline and Infrastructure Churn
11. Ownership / Attribution / ACH
12. Passive takeover exposure
13. Victimology / Objective / PIRs
14. IOC decisions / Gaps / Next Best Pivot / Action Matrix
15. Detection Engineering
16. Executive Assessment
17. Report Backend / Export Center / Case snapshot

## Performance

The notebook uses caps on dnstwist, urlscan details and pairwise domain comparisons. Large domain sets use candidate generation before similarity comparison. Optional internet-wide providers are queried only when their feature flag is enabled.

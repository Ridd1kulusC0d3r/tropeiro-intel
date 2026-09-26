# Tropeiro Intel 4.0 — Feature Validation Matrix

This document is the contract between the **Official Colab Investigation Station** and the Python backend.

| Capability | 4.0 status | Colab behavior |
|---|---|---|
| Multi-IOC ingestion | Implemented | Core |
| DNS / RDAP / CT | Implemented | Passive core |
| Wayback / Common Crawl | Implemented | Optional passive |
| urlscan search + Result API | Implemented | Passive, details bounded by limit |
| OTX / VT / ThreatFox | Implemented | VT/ThreatFox require optional secrets |
| DNSDumpster / FOFA / Censys | Implemented adapters | Optional secrets/flags |
| Provider query planner | Implemented | Skips missing/budgeted providers |
| dnstwist discovery | Implemented | Candidate generation with cap |
| Levenshtein / Jaro-Winkler / n-grams / token / TLD similarity | Implemented | Candidate relation only |
| Durable identifiers | Implemented | Extracted from passive scan artifacts |
| Passive web fingerprint | Implemented | No direct target fetch required |
| Evidence Ledger | Implemented | Provenance preserved |
| Source independence | Implemented | Source-family accounting |
| Relationship Graph 2.0 | Implemented | Typed / weighted edges |
| Cluster Explosion Guard | Implemented | Shared/common-only bridges suppressed |
| Campaign fingerprints | Implemented | Cluster-level |
| Operator fingerprints | Implemented | Separate from campaign fingerprint |
| Timeline | Implemented | Evidence-based |
| Infrastructure churn | Implemented | DNS/TLS/redirect change summary |
| Negative evidence | Implemented | Explicit absence taxonomy |
| ACH / competing hypotheses | Implemented | Same operator vs kit/hosting/reseller/coincidence |
| Attribution ladder | Implemented | Correlation kept separate from identity |
| Victimology / objective | Implemented | Conservative rule-based inference |
| MISP-style warning controls | Implemented | Local + ingestable warning-list entries |
| IOC Decision Engine | Implemented | Policy-controlled BLOCK/HUNT/MONITOR/etc. |
| IOC decay guidance | Implemented | Revalidation guidance by IOC mutability |
| Collection Gap Engine | Implemented | P1/P2 gaps |
| Next Best Pivot | Implemented | Utility / noise aware |
| Detection bridge | Implemented | Sigma, Splunk, Sentinel, Elastic, Wazuh, Suricata candidates |
| Passive dangling-CNAME exposure | Implemented | Detection only; no claiming/exploitation |
| Local enriched report | Implemented | Offline single HTML |
| Relationship graph / timeline in report | Implemented | Inline SVG, no CDN |
| Selective export | Implemented | HTML/JSON/CSV ZIP |
| Historical WHOIS / reverse WHOIS enterprise APIs | Provider slots only | Not required by public core; exact adapters require account-specific validation |
| Full live API integration test | Not asserted | CI uses unit/offline tests; credentials/network are external |

## Explicit non-claims

- Similarity does not establish maliciousness.
- A reused phishing kit does not establish a common operator.
- Shared hosting, ASN, registrar, CDN or DNS infrastructure does not establish campaign ownership.
- Missing RDAP registrant data does not establish concealment.
- Passive dangling-DNS evidence does not authorize claiming a resource.
- No-hit in a threat-intelligence source does not establish benignity.

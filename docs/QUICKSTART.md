# Quick Start

This guide takes a new analyst from an empty Colab session to a defensible investigation package.

## 1. Open the official notebook

[Open in Google Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)

Use **Runtime → Run all** only after reviewing the case configuration. Optional providers can consume quotas, and archaeology by billing statement is a poor incident-response technique.

## 2. Define the case

Minimum inputs:

```text
CASE_ID
SEEDS
```

Recommended context:

```text
BRAND
IMPERSONATED_ORG
CAMPAIGN_NOTE
LURE_TEXT
MANUAL_IOCS
```

`SEEDS` accepts domains or URLs separated by line breaks or commas.

## 3. Keep the passive baseline

Recommended initial configuration:

```python
ENABLE_DNSTWIST = True
ENABLE_WAYBACK = True
ENABLE_COMMONCRAWL = True
ENABLE_URLSCAN = True
ENABLE_OTX = True
ENABLE_VT = False
ENABLE_THREATFOX = False
ENABLE_HTTP_PROBE = False
```

Only enable direct HTTP probing for assets you are authorized to contact.

## 4. Add optional secrets

In Colab, open the **key icon → Secrets** and add only the providers you use:

```text
URLSCAN_API_KEY
VT_API_KEY
THREATFOX_AUTH_KEY
DNSDUMPSTER_API_KEY
FOFA_API_KEY
CENSYS_PAT
CENSYS_ORG_ID
```

Missing keys do not invalidate the case. Optional sources should be treated as enrichment, not as prerequisites.

## 5. Read results in this order

1. **Executive Assessment** – what the current evidence supports.
2. **Action Matrix** – what should happen now.
3. **IOC Decision Objects** – block/hunt/monitor/takedown posture.
4. **Campaign State** – lifecycle and temporal context.
5. **Attribution** – relationship confidence and competing hypotheses.
6. **Collection Gaps** – what is still unknown.
7. **Next Best Pivots** – where additional collection has the most value.
8. **Evidence Ledger** – provenance behind the conclusions.

## 6. Interpret scores correctly

Tropeiro distinguishes:

- investigation priority;
- confidence in an observation;
- source reliability;
- actionability;
- false-positive risk;
- attribution confidence.

A priority score is **not a probability of maliciousness**.

## 7. Export

The Reporting Edition produces a local, self-contained HTML report with an Export Center. Common packages:

### SOC package
- IOC Decisions CSV
- Action Matrix CSV
- Detection Package JSON

### Threat-intel package
- Executive Brief
- Evidence Ledger
- Attribution Assessment
- Collection Gaps
- STIX/MISP exports

### Management package
- Local HTML report
- Executive Brief
- Immediate actions

## 8. Preserve the case

Keep the generated package, timestamps and checksums together. The Evidence Ledger is what turns a screenshot-and-vibes investigation into something another analyst can reproduce.

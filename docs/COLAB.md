# Official Google Colab Machine

The official notebook is:

`notebooks/Tropeiro_Intel_Official_Colab.ipynb`

[Open it in Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/tropeiro-intel/blob/main/notebooks/Tropeiro_Intel_Official_Colab.ipynb)

## Design goals

The Colab build is deliberately:

- self-contained for the primary workflow;
- passive by default;
- CPU-only;
- usable without paid APIs;
- resilient when optional providers are unavailable;
- local-file based, with no external database requirement;
- exportable as JSON, CSV, STIX, MISP-like objects and HTML.

## Cell groups

| Group | Purpose |
|---|---|
| Installation | lightweight dependencies |
| Case configuration | seeds, brand, notes and feature flags |
| Ingestion | normalize domains, URLs and lure IOCs |
| Passive collection | DNS, RDAP, CT, historical sources |
| Threat intelligence | optional TI providers |
| Similarity / lookalikes | dnstwist-based candidate generation |
| Signal engineering | explainable investigative signals |
| Campaign graph | relationships and clustering |
| Evidence Ledger | provenance and reliability |
| Attribution | ownership, operator correlation and hypotheses |
| Decision intelligence | PIRs, gaps, pivots, IOC decisions and actions |
| Reporting | local interactive report and export center |

## Secrets

The public notebook reads optional values from Colab Secrets first, then environment variables, then leaves the provider disabled if no credential exists.

Never put API tokens into a public notebook cell and commit it. GitHub has enough accidental-secret archaeology already.

## Performance guidance

For large cases:

- reduce `DNSTWIST_MAX` during early triage;
- enable expensive providers only for high-value pivots;
- use campaign candidates before pairwise comparisons;
- preserve cache/snapshots when rerunning the same case;
- keep HTTP probing disabled unless necessary and authorized.

## Reproducibility

For a defensible case record, preserve:

- notebook version;
- case ID;
- configuration flags;
- source status;
- Evidence Ledger;
- export manifest/checksums;
- generated report.

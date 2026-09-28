# Campaign Memory & Cross-Case Intelligence — 4.4

Tropeiro Intel 4.4 adds a local, explainable memory of prior investigations.

## What it answers

- Have I seen this tracker, registrant, certificate, domain pattern or infrastructure before?
- Which previous cases share the most discriminating artifacts?
- Is a shared artifact rare in my own case history or common noise?
- Which historical relationships deserve analyst review?

Campaign Memory is not an attribution database. Similarity never becomes same-operator attribution automatically.

## Storage

Default Colab path: `/content/tropeiro_case_memory.sqlite`.

That file disappears when the runtime is deleted. For persistence between Colab sessions, mount Google Drive and set the memory path to a file under `/content/drive/MyDrive/`.

The database stays local to the path selected by the analyst.

## Artifacts retained

Campaign Memory can store normalized domains, URLs, IPs, hashes, public contacts already observed in the case, registration organizations, NS/MX/CNAME values, certificate names, trackers and selected fingerprints.

Unconfirmed GLiNER candidates are not written to Campaign Memory.

## Prevalence and rarity

Each artifact receives case frequency, prevalence, rarity and a base discrimination weight. Common infrastructure is deliberately downweighted.

## Cross-case similarity

Similarity uses a rarity-adjusted weighted Jaccard calculation. One shared artifact is capped, non-discriminating overlap is capped, and IP/ASN/provider/registrar-only overlap receives a stronger cap.

Every match explicitly sets `same_operator_inferred = false`.

## Python API

```python
from tropeiro.memory import CaseMemory

memory = CaseMemory('/path/to/tropeiro_case_memory.sqlite')
memory.import_case_json('previous_case.json')
```

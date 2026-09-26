# Arquitetura

## Camadas
1. Ingestão multi-IOC e lure text.
2. Coletores passivos.
3. Evidence Ledger com origem, tempo e confiabilidade da fonte.
4. Signal Engine e priorização explicável.
5. Campaign Graph e clustering.
6. Campaign Fingerprint.
7. Hunting passivo.
8. Timeline e snapshots.
9. Export STIX/MISP/JSON/CSV/HTML.

## Relações principais
- domain → IP
- domain → NS/MX
- domain → certificate
- URL → domain
- URL → phone/email
- URL → redirect → URL
- brand → lookalike candidate

## Regra analítica
Confiabilidade da fonte, confiança da observação e suspeição do IOC são dimensões diferentes.

## Attribution plane

```text
Evidence Ledger
   │
   ├─ Registration plane: RDAP / public entities
   ├─ Infrastructure plane: DNSDumpster / Censys / FOFA / DNS
   ├─ TLS plane: CT / Censys / FOFA
   ├─ Web plane: urlscan / FOFA / historical URLs
   └─ TI plane: VT / ThreatFox / URLhaus
          │
          ▼
   Entity Resolution
          │
          ▼
   Operator Fingerprint
          │
          ▼
   Competing Hypotheses
          │
          ▼
   Attribution Ladder
```

## Decision intelligence plane

```text
PIR / Intelligence Requirement
          |
          v
Collection Plan
          |
          v
Evidence + Attribution
          |
          +--> Warning Lists / FP controls
          |
          v
Analytical Assessments
          |
   +------+------+------+
   |             |      |
   v             v      v
Lifecycle   Victimology Objective
   |             |      |
   +------+------+------+
          |
          v
Multidimensional Confidence
          |
    +-----+-------+
    |             |
    v             v
IOC Decisions   Collection Gaps
    |             |
    v             v
Action Matrix   Next Best Pivot
    |
    v
Detection Engineering Bridge
    |
    v
Executive Intelligence Brief
```

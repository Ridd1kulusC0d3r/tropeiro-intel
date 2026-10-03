# Arquitetura

## Pipeline de investigação (4.8)

Interface, CLI e API Python usam **o mesmo pipeline** (`tropeiro/pipeline.py`); nenhuma lógica de investigação vive no front.

```text
 alvo (texto)
   │  targets.py        classifica (domínio, URL, IP, e-mail, hash, telefone, lote, isca) e extrai assuntos;
   │                    refang; plataformas legítimas e IPs não públicos viram contexto, não alvo
   ▼
 plano de fontes        onboarding.features_for_target + modo + chaves + profundidade → lista de tarefas
   │                    (uma por fonte × assunto) e linhas SKIPPED_* explicando o que ficou de fora
   ▼
 sources.py             executor concorrente: prazo total (45/90/180 s), TIMEOUT para o que não terminou,
   │                    UNAVAILABLE com mensagem legível, circuit breaker nos detalhes do urlscan
   ▼
 Evidence Ledger ──► decisões por IOC ──► extração de entidades (regras BR + GLiNER) ──► IA opcional (Qwen, verificada)
   ▼
 Campaign Memory (casos parecidos, iscas parecidas) ──► relatório HTML + STIX + MISP + Sigma + ZIP com manifest
```

| Módulo | Responsabilidade |
|---|---|
| `targets.py` | `classify`, `parse_target`, `registrable` |
| `onboarding.py` | `features_for_target`, `skip_reason`, `budget_limits` (qual fonte liga para qual tipo) |
| `sources.py` | `Task`, `run_tasks`, `describe_error`, estados de cada consulta |
| `pipeline.py` | `plan_investigation` (sem rede) e `investigate` (completo) |
| `enrichment.py` | respostas das fontes → `Observation` (domínio, IP, hash) |
| `doctor.py` | diagnóstico do ambiente e da rede |
| `frontend/` | Workbench (Gradio) e renderizadores; `cli.py`: `search`, `doctor`, `lure`, `workbench` |


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

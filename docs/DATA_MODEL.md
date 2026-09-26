# Modelo de dados

## Observation
`entity, entity_type, source, value, observed_at, confidence, notes`

## Evidence Ledger
Cada observação recebe `evidence_id` determinístico e pode ser persistida em SQLite.

## Campaign cluster
Componente conectado do grafo, resumido por domínios, URLs, IPs, telefones, certificados e força das relações.

## Fingerprint
Hash de características compostas da campanha. Serve para comparação temporal, não para atribuição automática.

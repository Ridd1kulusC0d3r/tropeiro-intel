# Attribution Engineering

Tropeiro Intel separates four questions:

1. **Infrastructure ownership** — who operates the ASN, netblock, hosting or registrar.
2. **Asset ownership** — what organization is publicly attached to domain/certificate/asset records.
3. **Operator correlation** — whether campaigns show evidence of common operational control.
4. **Actor attribution** — whether public, independent evidence supports association to a known actor.

## Attribution ladder
- L0 Observed
- L1 Related
- L2 Infrastructure cluster
- L3 Operator cluster
- L4 Entity attribution
- L5 Known actor attribution

The tool must not jump from shared IP/ASN/provider to a person or actor identity.

## Strong correlation signals
Public email/phone reuse, tracking identifiers, registrant organization, unusual certificate reuse,
redirect-chain reuse and distinctive web/template fingerprints.

## Weak signals
Shared IP, ASN, hosting provider, registrar or TLD. These may be useful pivots, but are insufficient alone.

## Competing hypotheses
The engine explicitly compares:
- H1 same operator
- H2 shared phishing kit
- H3 shared hosting
- H4 reseller/infrastructure reuse
- H5 coincidence

## Privacy
Raw contact identifiers can be retained in the local evidence store when lawfully collected.
Reports should use stable hashed references by default.

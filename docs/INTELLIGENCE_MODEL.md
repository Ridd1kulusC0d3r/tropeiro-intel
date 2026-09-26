# Intelligence Model

Tropeiro Intel is built around a simple rule: **data collection is not intelligence**.

```text
DATA
  ↓
OBSERVATIONS
  ↓
EVIDENCE + PROVENANCE
  ↓
RELATIONSHIPS
  ↓
ANALYTICAL JUDGMENTS
  ↓
DECISIONS
  ↓
ACTIONS
  ↓
FEEDBACK / NEXT COLLECTION
```

## Four attribution layers

### 1. Infrastructure ownership
Who officially controls an IP range, ASN, hosting platform, registrar or other infrastructure component?

### 2. Asset ownership
Which organization is publicly associated with a domain, certificate, account or resource?

### 3. Operator correlation
Do multiple campaigns appear to be operated by the same entity based on independent, discriminating signals?

### 4. Actor attribution
Is there sufficient public evidence to associate the operator with a named threat actor or real-world entity?

These layers must not be collapsed.

## Evidence strength

Typical examples:

**Very strong**
- same unusual durable tracker/account identifier;
- same public contact identifier with independent corroboration;
- same rare operational certificate/key material;
- independently verified registrant organization reuse.

**Strong**
- repeated unusual redirect pattern;
- same distinctive phishing-kit fingerprint;
- stable reusable infrastructure across time;
- multiple temporally aligned identifiers.

**Moderate**
- uncommon NS/MX pair;
- ASN + temporal + registration pattern;
- repeated registrar/registration behavior.

**Weak**
- same IP;
- same ASN;
- same hosting provider;
- same TLD;
- same popular registrar.

Multiple independent signals matter more than one superficially dramatic signal.

## Attribution ladder

```text
LEVEL 0  OBSERVED
LEVEL 1  RELATED
LEVEL 2  INFRASTRUCTURE CLUSTER
LEVEL 3  OPERATOR CLUSTER
LEVEL 4  ENTITY ATTRIBUTION
LEVEL 5  ACTOR ATTRIBUTION
```

A ladder level expresses what the evidence supports, not how exciting the case feels.

## Competing hypotheses

Tropeiro keeps alternatives visible:

```text
H1 same operator
H2 shared phishing kit
H3 shared hosting / provider
H4 resold or delegated infrastructure
H5 coincidence
```

Evidence is assessed against all hypotheses rather than only the analyst's favorite one.

## Actionability

IOC decisions combine, at minimum:

```text
confidence
recency / activity
source diversity
false-positive risk
shared-infrastructure caution
campaign context
evidence count
```

Operational actions are kept separate from attribution conclusions.

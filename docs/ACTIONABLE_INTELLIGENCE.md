# Tropeiro Intel — Actionable Intelligence Model

## The analytical contract
Every important finding should be able to flow through:

```text
Observation
  -> Assessment
  -> Implication
  -> Decision
  -> Action
  -> Owner
  -> Evidence
  -> Feedback
```

A checklist result is not an intelligence product.

## Core engines
1. Intelligence Requirements / PIRs
2. Collection Plan
3. Collection Gap Engine
4. Next Best Pivot
5. IOC Decision Objects
6. Action Matrix
7. Detection Engineering Bridge
8. Campaign Lifecycle
9. Infrastructure Churn
10. Victimology
11. Objective Assessment
12. Multidimensional Confidence
13. Warning Lists / False-Positive Controls
14. Executive Intelligence Brief

## Decision thresholds
The tool intentionally distinguishes:
- **confidence**: support for the analytical judgment;
- **actionability**: whether an IOC is safe/useful to act upon;
- **severity**: potential impact;
- **activity**: whether infrastructure appears current;
- **false-positive risk**: risk of harming legitimate/shared infrastructure.

No single score should substitute these dimensions.

## Intelligence Requirements
Default PIRs ask:
- Is the campaign still active?
- Are new assets appearing?
- Which IOCs are safe to block?
- Is takedown evidence sufficient?
- Who/what is targeted?
- Is there common operational control?
- What is the next best pivot?
- What gaps prevent stronger conclusions?

## Warning-list semantics
Warning hits mean **caution**, not benignity. Shared cloud/CDN, public resolvers and other
widely-used infrastructure should not be promoted to operator attribution or automatic blocking
without discriminating evidence.

## Detection bridge
The system can generate candidates for DNS/proxy/email hunts and experimental Sigma/Splunk/KQL
content. Generated detections require analyst validation and environment-specific field mapping.

# Roadmap

The next releases prioritize **relationship quality over API count**.

## Near term

- expanded domain-similarity engine: homoglyph, lexical, token and TLD similarity;
- durable identifier extraction from passive web-scan data;
- source-dependency graph and stronger independence accounting;
- negative-evidence model;
- historical WHOIS / passive-DNS provider adapters;
- prevalence-aware edge weighting and cluster-explosion controls;
- richer infrastructure-churn analysis;
- confidence calibration against labeled historical cases;
- Elastic, Wazuh and Suricata detection adapters;
- analyst overrides with audit trail.

## Advanced

- campaign/operator fingerprints across historical cases;
- knowledge-graph persistence and case-to-case comparison;
- evidence-linked executive judgments;
- historical baselines for infrastructure commonness;
- multilingual phishing-kit fingerprinting;
- passive dangling-DNS exposure detection for authorized defensive review.

## What will not become a core dependency

Paid internet-intelligence providers remain adapters. The public Colab must continue to function without enterprise subscriptions, GPU resources or an external database.

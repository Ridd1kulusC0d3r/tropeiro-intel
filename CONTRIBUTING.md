# Contributing

Contributions should improve reproducibility, evidence quality, analyst usability or defensive coverage.

## Development setup

```bash
git clone https://github.com/Ridd1kulusC0d3r/tropeiro-intel.git
cd tropeiro-intel
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,colab]"
pytest -q
```

## Pull-request expectations

- keep passive defaults intact;
- do not hardcode API keys;
- add tests for new normalization/scoring logic;
- document new evidence fields and source semantics;
- do not equate shared infrastructure with operator identity;
- preserve backward compatibility where practical;
- include a clear failure mode when optional providers are unavailable.

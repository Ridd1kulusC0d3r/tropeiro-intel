# Troubleshooting

## A provider returns nothing

“No result” can mean:

- no data exists;
- the provider does not index that data;
- quota/authentication failed;
- the artifact is too new or too old;
- collection timed out;
- the provider schema changed.

Treat absence as a collection result, not as proof of benignity.

## `dnstwist` is slow

Reduce `DNSTWIST_MAX` during triage. Expand only after the root domain/brand is confirmed relevant.

## Censys / FOFA / DNSDumpster cells do not run

They are optional. Confirm the provider flag is enabled and the secret exists. The rest of the notebook should remain usable without them.

## `pytest` cannot import `tropeiro`

From a clone, install the package or use the project root:

```bash
pip install -e ".[dev]"
pytest -q
```

The repository config also includes the project root in pytest's Python path.

## HTML report is empty

Confirm the case reached the intelligence/reporting cells and that `REPORT_DATA` contains the expected sections. Earlier collector failures should appear under source status rather than silently disappearing.

## Colab runtime was reset

Colab storage is ephemeral. Re-run installation/configuration and regenerate outputs, or persist the final case package to Drive manually.

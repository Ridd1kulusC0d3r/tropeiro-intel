# Troubleshooting

## Minha busca não funciona ou parece travada

Faça nesta ordem (leva 1 minuto):

1. **Diagnostique:** `tropeiro doctor` (ou, no Workbench, *Diagnóstico do ambiente → Rodar diagnóstico*). Ele testa Python, dependências, pastas e a rede até cada fonte, e diz o que corrigir.
2. **Tente sem interface:** `tropeiro search example.com`. Se funcionar, o problema está na interface/navegador; se não, está no ambiente/rede.
3. **Leia o estado de cada fonte** (*Dados → Saúde das fontes* ou o terminal): `UNAVAILABLE` mostra o motivo, `TIMEOUT` indica prazo estourado, `SKIPPED_*` não é erro.

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `tropeiro search` sai com código **2**: "nenhuma fonte respondeu" | sem internet ou proxy bloqueando | `tropeiro doctor`; configure `HTTPS_PROXY` ou libere os domínios das fontes |
| Várias fontes `UNAVAILABLE` com `falha de rede` | firewall/proxy corporativo, ou a fonte caiu | veja qual falha no `doctor`; as demais fontes continuam valendo |
| `Wayback` sempre `UNAVAILABLE` | o Wayback é instável e alguns proxies o bloqueiam | normal; a busca segue sem ele |
| `crt.sh` `HTTP 502/404` | o crt.sh fica sobrecarregado | já há uma nova tentativa; repita em alguns minutos |
| `urlscan:detalhes` `HTTP 403` | o urlscan pode exigir chave para os detalhes | defina `URLSCAN_API_KEY` (opcional); a busca do urlscan em si funciona |
| Resultado diz `TIMEOUT` | alguma fonte passou do prazo (45/90/180 s) | o resultado é parcial e válido; aumente `--budget` ou `--deadline` |
| A tela do Workbench fica **sem resultado e sem erro** | versões anteriores à 4.8: o Gradio recusava servir os arquivos exportados (`InvalidPathError`) | atualize (`git pull && pip install -e ".[colab]"`) |
| No **Colab**, a interface não aparece | o Gradio precisa de link público no Colab; versões antigas forçavam `share=False` | atualize; execute a célula 06A de novo |
| `localhost refused` / porta ocupada | outra instância usando a porta | `tropeiro workbench` agora escolhe a primeira porta livre |
| Demora mais de 1 minuto em um domínio | fontes lentas em série (versões antigas) | atualize: a coleta agora é paralela, com prazo |


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


## `ModuleNotFoundError: No module named 'tropeiro'`

This means the backend bootstrap did not complete, or the Colab runtime retained an incomplete clone.

Version 4.0.1 makes cells 01 and 02 self-healing. Recommended recovery:

1. Use **Runtime → Disconnect and delete runtime**.
2. Reopen the official notebook from GitHub.
3. Run cell **01 · Bootstrap robusto do backend oficial**.
4. Confirm cell 02 reports `repo: true` and a `tropeiro_path` under `/content/tropeiro-intel`.
5. Only then continue or use **Run all**.

The bootstrap now removes an incomplete `/content/tropeiro-intel` directory, adds the source tree to `sys.path`, installs core dependencies first, and treats Colab extras as best-effort.

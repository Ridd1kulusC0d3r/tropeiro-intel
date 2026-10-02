# Contribuindo

Contribuições devem melhorar **reprodutibilidade, qualidade da evidência, usabilidade para o analista ou cobertura defensiva**. Documentação em [`docs/`](docs/README.md).

## Ambiente de desenvolvimento

```bash
git clone https://github.com/Ridd1kulusC0d3r/tropeiro-intel.git
cd tropeiro-intel
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,colab]"
pytest -q                                     # offline; deve passar sem rede
ruff check --select E9,F63,F7,F82 .           # o mesmo lint da CI
```

## Princípios (não negociáveis)

1. **Passivo por padrão.** Sondagem direta só com `AUTHORIZED_ACTIVE` + `enable_http_probe`.
2. **Nada derivado de IA escreve no Evidence Ledger.** Saídas de modelo são candidatos (`derived=True`, `analyst_confirmed=False`).
3. **Correlação não é identidade.** Infraestrutura compartilhada não prova operador comum.
4. **Texto externo é escapado** em HTML (`html.escape`) e hostnames passam por `valid_hostname` antes de entrar em URL.
5. **Sem chaves no código.** Use as variáveis de [CONFIGURATION](docs/CONFIGURATION.md).
6. **Falha clara** quando uma fonte opcional não está disponível (status `UNAVAILABLE`, não exceção silenciosa).

## Receitas para contribuir

### Adicionar uma marca/tema de isca

Edite `RULES` em `tropeiro/intelligence/br_lures.py`: `("Marca", "tema", ["palavra-chave em minúsculas", ...])`. Prefira frases a palavras soltas (reduz falso positivo). Acrescente um caso a `tests/test_v45_additions.py`.

### Adicionar uma plataforma legítima

Inclua o domínio em `KNOWN_LEGIT` (e em `MESSAGING` se o IOC útil for o número/conta) em `tropeiro/intelligence/legit_domains.py`, com teste.

### Adicionar um coletor

1. Crie `tropeiro/collectors/<fonte>.py` usando `from ..http import get` (retry, limite por host e cache já vêm de graça). Valide o alvo com `valid_hostname`.
2. Declare a confiabilidade padrão em `Settings.source_reliability`.
3. Se exigir chave, leia de variável de ambiente/Colab Secret e documente em [CONFIGURATION](docs/CONFIGURATION.md).
4. Teste com resposta simulada (monkeypatch de `tropeiro.http.request`): **sem rede nos testes**.
5. Registre o status (`OK`/`UNAVAILABLE`) como as demais fontes.

### Alterar a política de decisão

Mude `DEFAULT_POLICY` só com justificativa de falso positivo e atualize [INTERPRETING_RESULTS](docs/INTERPRETING_RESULTS.md).

## Documentação

- Exemplos em ` ```python ` dentro de `docs/` são **executados** por `tests/test_docs.py`: precisam rodar offline e terminar com `assert`.
- Trecho ilustrativo que não deve rodar (depende de arquivo, de Colab, de estado global): use ` ```python no-run `.
- Links relativos e âncoras (`arquivo.md#titulo`) entre documentos são verificados.
- Todo `docs/*.md` novo deve aparecer em [`docs/README.md`](docs/README.md).
- Valores de exemplo: domínios `.example`, IPs `203.0.113.0/24`. Nunca dados reais de vítimas.

## Pull requests

- uma mudança por PR, com teste do comportamento novo;
- `pytest -q` e o lint passando;
- descreva falhas conhecidas e o que **não** foi testado (por exemplo, modelos reais);
- preserve compatibilidade quando possível (`render_outputs`, `Settings`, formatos exportados).

O template de PR lembra desses pontos.

## Segurança e conduta

Veja [SECURITY.md](SECURITY.md) e [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Vulnerabilidades: aviso privado de segurança no GitHub, nunca em issue pública.

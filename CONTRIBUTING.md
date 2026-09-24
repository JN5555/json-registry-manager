# Contributing

Contributions are welcome.

## Development setup

```bash
git clone https://github.com/JN5555/json-registry-manager.git
cd json-registry-manager
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

## Before opening a pull request

Run:

```bash
pytest -q
jrm --config examples/phishing-domain-guard/registry.yaml validate
```

Please keep stored registry values language-neutral. UI text belongs in the translation files under `src/json_registry_manager/i18n/`.

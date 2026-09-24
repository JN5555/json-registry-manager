# JSON Registry Manager

[Česky](README.cs.md)

**JSON Registry Manager (JRM)** is a schema-driven interactive CLI for managing, validating, and versioning structured JSON registries.

It is designed for projects where a JSON file is maintained as a human-curated registry: protected domains, service catalogs, allowlists, API endpoints, dictionaries, inventories, or similar structured data.

The application itself does not know what a bank, domain, server, or media outlet is. A small `registry.yaml` file defines the fields, validation rules, labels, and registry location.

## Features

- interactive terminal UI
- English and Czech UI
- automatic language detection from the operating system
- persistent language setting (`auto`, `en`, `cs`)
- one-run language override with `--lang`
- add, edit, remove, search, and list entries
- required-field validation
- unique IDs and values
- hostname validation
- choice fields with localized labels
- automatic slug generation for IDs
- Git diff, commit, and push helpers
- non-interactive validation for CI
- GitHub Actions example
- configuration-driven design reusable across projects

## Requirements

- Python 3.10 or newer
- Git is optional, but required for Git integration

## Installation

### Recommended: pipx

On Fedora:

```bash
sudo dnf install pipx
pipx ensurepath
pipx install git+https://github.com/JN5555/json-registry-manager.git
```

Open a new terminal and verify:

```bash
jrm --version
```

Upgrade later:

```bash
pipx upgrade json-registry-manager
```

### Without pipx

Clone the repository and use the included user installer. It creates an isolated virtual environment under `~/.local/share/json-registry-manager/` and exposes `jrm` through `~/.local/bin/jrm`:

```bash
git clone https://github.com/JN5555/json-registry-manager.git
cd json-registry-manager
./scripts/install-user.sh
```

If `~/.local/bin` is not in your `PATH`, add this to `~/.bashrc` and open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

To update this installation later:

```bash
cd /path/to/json-registry-manager
git pull
./scripts/install-user.sh
```

To uninstall:

```bash
./scripts/uninstall-user.sh
```

### Development install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Quick start

The easiest way to prepare a new project is now:

```bash
cd /path/to/your-project
jrm init
```

The wizard can use an existing JSON file or create a new one, detect a root list of objects, infer existing fields, and create `registry.yaml`. If you simply run `jrm` in a directory without `registry.yaml`, JRM offers to initialize the project automatically.

Example:

```bash
mkdir my-url-tool
cd my-url-tool
jrm init
jrm validate
jrm
```

A registry project needs two files:

```text
registry.yaml
registry.json
```

Run JRM from the project directory:

```bash
jrm
```

Or explicitly select a configuration:

```bash
jrm --config path/to/registry.yaml
```

## Language

JRM supports English and Czech.

By default it uses automatic language detection based on `LC_ALL`, `LC_MESSAGES`, `LANG`, and the system locale.

Choose a language permanently:

```bash
jrm language cs
jrm language en
jrm language auto
```

Override it for one command only:

```bash
jrm --lang cs validate
jrm --lang en validate
```

The persistent setting is stored in:

```text
~/.config/json-registry-manager/config.toml
```

or below `$XDG_CONFIG_HOME` when that variable is set.

## Commands

Start the interactive interface:

```bash
jrm
```

List entries:

```bash
jrm list
```

Validate a registry:

```bash
jrm validate
```

Search:

```bash
jrm search airbank
```

Add an entry:

```bash
jrm add
```

Edit by ID:

```bash
jrm edit airbank
```

Remove by ID:

```bash
jrm remove airbank
```

Show Git changes:

```bash
jrm diff
```

Commit the registry file:

```bash
jrm commit "Add Example Bank"
```

Push the current branch:

```bash
jrm push
```

## Configuration

### Field help and examples

Profiles can provide localized explanations and examples for each field. This keeps the core tool generic while making project-specific forms understandable to non-technical users.

```yaml
fields:
  domains:
    type: list
    required: true
    validator: hostname
    label:
      en: Official main domain(s)
      cs: Oficiální hlavní doména / domény
    help:
      en: Main legitimate websites. Full URLs are accepted and normalized.
      cs: Hlavní legitimní weby služby. Lze vložit i celou URL.
    example:
      en: example.com
      cs: priklad.cz
```

Interactive forms clearly mark required and optional fields. Optional fields can be skipped with Enter.


Example `registry.yaml`:

```yaml
name: Example Registry
file: registry.json
items_key: entities
id_field: id
display_field: name
metadata_date_field: updated

fields:
  name:
    type: string
    required: true
    label:
      en: Name
      cs: Název

  id:
    type: slug
    required: true
    unique: true
    label:
      en: ID
      cs: ID

  category:
    type: choice
    required: true
    values:
      - service
      - website
    value_labels:
      service:
        en: Service
        cs: Služba
      website:
        en: Website
        cs: Web

  domains:
    type: list
    required: true
    validator: hostname
    unique: true
    label:
      en: Domains
      cs: Domény
```

Supported field types:

- `string`
- `slug`
- `choice`
- `list`
- `boolean`
- `integer`

Current built-in validator:

- `hostname`

In the interactive editor, hostname fields also accept pasted URLs such as `https://online.example.com/login` or `online.example.com/login`. JRM normalizes them to `online.example.com` before saving. Registry files themselves remain strict: a manually stored value containing a path still fails validation. If an entry fails validation, the editor keeps all entered values and offers an in-place correction instead of discarding the form.

Options:

- `required: true` — field cannot be empty
- `unique: true` — value may occur only once across the registry
- `values:` — allowed values for a `choice` field
- `value_labels:` — localized display names while preserving language-neutral stored values
- `label:` — localized field name

## JSON format

JRM preserves the root JSON object and edits only the list specified by `items_key`.

Example:

```json
{
  "schema": 1,
  "updated": "2026-09-24",
  "entities": [
    {
      "id": "example",
      "name": "Example",
      "domains": ["example.com"]
    }
  ]
}
```

When `metadata_date_field` is configured, JRM updates that root field to the current date whenever the registry is saved.

## Phishing Domain Guard example

A ready-to-use profile is included in:

```text
examples/phishing-domain-guard/
```

It contains:

- `registry.yaml`
- `protected-list.json`
- `protected-list.schema.json`

To use JRM with the real [Phishing Domain Guard](https://github.com/JN5555/phishing-domain-guard) repository, copy the example `registry.yaml` into its repository root:

```bash
cp examples/phishing-domain-guard/registry.yaml /path/to/phishing-domain-guard/registry.yaml
```

Then run from the Phishing Domain Guard repository:

```bash
jrm
```

JRM will edit its existing `protected-list.json`.

## Continuous validation with GitHub Actions

Because `jrm validate` returns a non-zero exit code when validation fails, it can be used in CI.

Example:

```yaml
name: Validate registry

on:
  push:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - run: pip install git+https://github.com/JN5555/json-registry-manager.git
      - run: jrm validate
```

## Development

Clone the repository:

```bash
git clone https://github.com/JN5555/json-registry-manager.git
cd json-registry-manager
```

Create a virtual environment and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run tests:

```bash
pytest -q
```

Validate the included example:

```bash
jrm --config examples/phishing-domain-guard/registry.yaml validate
```

## Adding another language

Translation files are stored in:

```text
src/json_registry_manager/i18n/
```

English and Czech are currently included:

```text
en.json
cs.json
```

The program keeps stored registry values language-neutral. Only interface labels are translated.

## Security model

JRM does not connect to GitHub APIs and does not store GitHub credentials.

Git operations use the locally installed `git` command and its existing authentication configuration.

Registry data is read and written locally. Network access is only performed indirectly when the user explicitly runs Git commands such as `git push` through JRM.

## License

MIT

## Interactive interface

The interactive UI includes an adaptive **Browse entries** view. Long registries are rendered in 1–3 columns depending on terminal width. Large selection lists use type-to-filter autocomplete. Search results are actionable: select a result and choose **Show details**, **Edit**, **Remove**, or **Back**.


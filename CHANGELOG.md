# Changelog

## 0.2.0 - 2026-09-24

- Added `jrm init` interactive project initializer.
- Detects existing JSON registries and root object-list keys.
- Infers existing fields and creates a starter `registry.yaml`.
- `jrm` now offers initialization when no configuration exists.
- Added user-level installer/uninstaller scripts for systems without pipx.
- Version reporting now uses installed package metadata to avoid duplicate version drift.
- Updated installation documentation and GitHub Actions runner/action versions.

## 0.1.3 - 2026-09-24

- Added adaptive 1–3 column registry overview for long lists.
- Added Browse entries to the interactive menu.
- Large entry selectors now support type-to-filter autocomplete.
- Search results now offer Detail, Edit, Remove, and Back actions.
- Added localized entry detail view.

## 0.1.2 - 2026-09-24

- Add localized per-field help and examples driven by `registry.yaml`.
- Mark fields clearly as required or optional in interactive forms.
- Replace technical Phishing Domain Guard labels with user-facing wording.
- Explain optional login/host and protected-name fields directly in the form.
- Improve category labels for finance-related services.

## 0.1.1 - 2026-09-24

- Accept pasted URLs in hostname fields and store only the hostname.
- Preserve entered form values when validation fails and offer an in-place correction flow.
- Show hostname normalization in the interactive editor.

## 0.1.0 - 2026-09-24

Initial public release.

- schema-driven JSON registry configuration
- interactive and command-line workflows
- English and Czech UI
- automatic system-language detection
- validation for required fields, IDs, unique values and hostnames
- Git diff, commit and push helpers
- GitHub Actions validation example
- Phishing Domain Guard example profile

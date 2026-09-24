from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from .i18n import Translator
from .prompts import Choice, confirm, select, text

console = Console()

FIELD_TYPES = ["string", "slug", "choice", "list", "boolean", "integer"]


def _nonempty(value: Any) -> bool:
    return value not in (None, "", [])


def _infer_type(name: str, values: list[Any], id_field: str) -> str:
    if name == id_field:
        return "slug"
    samples = [v for v in values if v is not None]
    if samples and all(isinstance(v, bool) for v in samples):
        return "boolean"
    if samples and all(isinstance(v, int) and not isinstance(v, bool) for v in samples):
        return "integer"
    if samples and all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in samples):
        return "list"
    return "string"


def discover_registry_lists(data: dict[str, Any]) -> list[str]:
    """Return root keys that look like a registry list (empty or list of objects)."""
    out: list[str] = []
    for key, value in data.items():
        if isinstance(value, list) and (not value or all(isinstance(item, dict) for item in value)):
            out.append(str(key))
    return out


def infer_fields(items: list[dict[str, Any]], id_field: str = "id", display_field: str = "name") -> dict[str, dict[str, Any]]:
    """Infer a conservative field configuration from existing entries."""
    names: list[str] = []
    for item in items[:100]:
        for key in item:
            if key not in names:
                names.append(key)
    fields: dict[str, dict[str, Any]] = {}
    for name in names:
        values = [item.get(name) for item in items[:100] if name in item]
        cfg: dict[str, Any] = {
            "type": _infer_type(name, values, id_field),
            "required": bool(items) and all(name in item and _nonempty(item.get(name)) for item in items[:100]),
        }
        if name == id_field:
            cfg["required"] = True
            cfg["unique"] = True
        if name == display_field:
            cfg["required"] = True
        fields[name] = cfg
    return fields


def default_fields() -> dict[str, dict[str, Any]]:
    return {
        "name": {
            "type": "string",
            "required": True,
            "label": {"en": "Name", "cs": "Název"},
        },
        "id": {
            "type": "slug",
            "required": True,
            "unique": True,
            "label": {"en": "ID", "cs": "ID"},
        },
    }


def write_project_files(
    config_path: Path,
    registry_path: Path,
    config_data: dict[str, Any],
    registry_data: dict[str, Any] | None,
    *,
    overwrite_registry: bool = False,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if registry_data is not None and (overwrite_registry or not registry_path.exists()):
        registry_path.write_text(json.dumps(registry_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _field_wizard(lang: str) -> tuple[str, dict[str, Any]] | None:
    cs = lang == "cs"
    name = (text("Název pole" if cs else "Field name") or "").strip()
    if not name:
        return None
    ftype = select(
        "Typ pole" if cs else "Field type",
        [Choice(t, t) for t in FIELD_TYPES],
        default="string",
    ) or "string"
    cfg: dict[str, Any] = {"type": ftype}
    cfg["required"] = bool(confirm("Povinné pole?" if cs else "Required field?", default=False))
    if confirm("Musí být hodnota unikátní?" if cs else "Must the value be unique?", default=False):
        cfg["unique"] = True
    if ftype == "choice":
        raw = text("Povolené hodnoty (oddělte čárkami)" if cs else "Allowed values (comma separated)") or ""
        cfg["values"] = [v.strip() for v in raw.split(",") if v.strip()]
    if ftype in {"string", "list"}:
        validator = select(
            "Validace" if cs else "Validation",
            [
                Choice("Žádná" if cs else "None", ""),
                Choice("Doména / hostname", "hostname"),
            ],
            default="",
        )
        if validator:
            cfg["validator"] = validator
    help_text = (text("Krátká nápověda (volitelné)" if cs else "Short help (optional)") or "").strip()
    if help_text:
        cfg["help"] = {lang: help_text}
    example = (text("Příklad (volitelné)" if cs else "Example (optional)") or "").strip()
    if example:
        cfg["example"] = {lang: example}
    return name, cfg


def init_project(config_path: str | Path, tr: Translator, force: bool = False) -> int:
    """Interactive initializer for a registry project."""
    cfg_path = Path(config_path).expanduser().resolve()
    base = cfg_path.parent
    cs = tr.language == "cs"

    if cfg_path.exists() and not force:
        console.print(f"[red]{tr.t('init.config_exists', path=cfg_path)}[/red]")
        return 1

    console.print(f"[bold]{tr.t('init.title')}[/bold]")
    project_name = (text(tr.t("init.project_name"), default=base.name) or base.name).strip()

    json_files = sorted(p for p in base.glob("*.json") if p.is_file())
    mode = "new"
    chosen: Path | None = None
    if json_files:
        choices = [Choice(f"{tr.t('init.use_existing')}: {p.name}", p) for p in json_files]
        choices.append(Choice(tr.t("init.create_new"), None))
        chosen = select(tr.t("init.registry_source"), choices)
        if chosen is not None:
            mode = "existing"

    if mode == "existing" and chosen is not None:
        registry_path = chosen.resolve()
        try:
            registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            console.print(f"[red]{tr.t('init.invalid_json', message=exc)}[/red]")
            return 1
        if not isinstance(registry_data, dict):
            console.print(f"[red]{tr.t('init.root_object')}[/red]")
            return 1
        candidates = discover_registry_lists(registry_data)
        if len(candidates) == 1:
            items_key = candidates[0]
        elif candidates:
            items_key = select(tr.t("init.items_key"), [Choice(k, k) for k in candidates]) or candidates[0]
        else:
            items_key = (text(tr.t("init.items_key"), default="items") or "items").strip()
            registry_data.setdefault(items_key, [])
        current_items = registry_data.get(items_key, [])
        if not isinstance(current_items, list) or any(not isinstance(x, dict) for x in current_items):
            console.print(f"[red]{tr.t('init.items_invalid', key=items_key)}[/red]")
            return 1
    else:
        filename = (text(tr.t("init.registry_file"), default="registry.json") or "registry.json").strip()
        registry_path = (base / filename).resolve()
        if registry_path.exists() and not force:
            console.print(f"[red]{tr.t('init.registry_exists', path=registry_path)}[/red]")
            return 1
        items_key = (text(tr.t("init.items_key"), default="items") or "items").strip()
        registry_data = {items_key: []}
        current_items: list[dict[str, Any]] = []

    known_fields: list[str] = []
    for item in current_items[:100]:
        for key in item:
            if key not in known_fields:
                known_fields.append(key)

    default_id = "id" if "id" in known_fields or not known_fields else known_fields[0]
    id_field = (text(tr.t("init.id_field"), default=default_id) or default_id).strip()
    default_display = "name" if "name" in known_fields or not known_fields else id_field
    display_field = (text(tr.t("init.display_field"), default=default_display) or default_display).strip()

    use_date = confirm(tr.t("init.use_date"), default=("updated" in registry_data))
    metadata_date_field: str | None = None
    if use_date:
        metadata_date_field = (text(tr.t("init.date_field"), default="updated") or "updated").strip()
        registry_data.setdefault(metadata_date_field, date.today().isoformat())

    fields = infer_fields(current_items, id_field=id_field, display_field=display_field) if current_items else default_fields()
    if id_field not in fields:
        fields[id_field] = {"type": "slug", "required": True, "unique": True}
    if display_field not in fields:
        fields[display_field] = {"type": "string", "required": True}

    if fields:
        console.print(f"[dim]{tr.t('init.detected_fields', fields=', '.join(fields))}[/dim]")

    while confirm(tr.t("init.add_field"), default=False):
        result = _field_wizard(tr.language)
        if result:
            field_name, field_cfg = result
            fields[field_name] = field_cfg

    config_data: dict[str, Any] = {
        "name": project_name,
        "file": str(registry_path.relative_to(base)) if registry_path.is_relative_to(base) else str(registry_path),
        "items_key": items_key,
        "id_field": id_field,
        "display_field": display_field,
        "metadata_date_field": metadata_date_field,
        "fields": fields,
    }
    # Keep the generated YAML tidy: null means no automatic date update.
    if metadata_date_field is None:
        config_data["metadata_date_field"] = None

    write_project_files(
        cfg_path,
        registry_path,
        config_data,
        registry_data if mode == "new" else None,
        overwrite_registry=force and mode == "new",
    )
    console.print(f"[green]✓ {tr.t('init.created_config', path=cfg_path.name)}[/green]")
    if mode == "new":
        console.print(f"[green]✓ {tr.t('init.created_registry', path=registry_path.name)}[/green]")
    else:
        console.print(f"[green]✓ {tr.t('init.using_registry', path=registry_path.name)}[/green]")
    console.print(f"[dim]{tr.t('init.next_step')}[/dim]")
    return 0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FieldConfig:
    name: str
    type: str = "string"
    required: bool = False
    label: dict[str, str] | str | None = None
    values: list[str] = field(default_factory=list)
    value_labels: dict[str, dict[str, str] | str] = field(default_factory=dict)
    validator: str | None = None
    unique: bool = False
    default: Any = None
    help: dict[str, str] | str | None = None
    example: dict[str, str] | str | None = None

    def label_for(self, lang: str) -> str:
        if isinstance(self.label, dict):
            return self.label.get(lang) or self.label.get("en") or self.name
        return self.label or self.name

    def help_for(self, lang: str) -> str | None:
        if isinstance(self.help, dict):
            return self.help.get(lang) or self.help.get("en")
        return self.help

    def example_for(self, lang: str) -> str | None:
        if isinstance(self.example, dict):
            return self.example.get(lang) or self.example.get("en")
        return self.example


@dataclass
class RegistryConfig:
    path: Path
    name: str
    file: Path
    items_key: str = "entities"
    id_field: str = "id"
    display_field: str = "name"
    metadata_date_field: str | None = "updated"
    fields: list[FieldConfig] = field(default_factory=list)

    @property
    def base_dir(self) -> Path:
        return self.path.parent

    @property
    def registry_path(self) -> Path:
        return (self.base_dir / self.file).resolve()

    def field(self, name: str) -> FieldConfig | None:
        return next((f for f in self.fields if f.name == name), None)


def load_config(path: str | Path = "registry.yaml") -> RegistryConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(config_path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    fields_raw = raw.get("fields") or {}
    fields: list[FieldConfig] = []
    for name, cfg in fields_raw.items():
        cfg = cfg or {}
        fields.append(
            FieldConfig(
                name=name,
                type=str(cfg.get("type", "string")),
                required=bool(cfg.get("required", False)),
                label=cfg.get("label"),
                values=list(cfg.get("values") or []),
                value_labels=dict(cfg.get("value_labels") or {}),
                validator=cfg.get("validator"),
                unique=bool(cfg.get("unique", False)),
                default=cfg.get("default"),
                help=cfg.get("help"),
                example=cfg.get("example"),
            )
        )
    return RegistryConfig(
        path=config_path,
        name=str(raw.get("name") or config_path.parent.name),
        file=Path(str(raw.get("file") or "registry.json")),
        items_key=str(raw.get("items_key") or "entities"),
        id_field=str(raw.get("id_field") or "id"),
        display_field=str(raw.get("display_field") or "name"),
        metadata_date_field=(str(raw["metadata_date_field"]) if raw.get("metadata_date_field") else None),
        fields=fields,
    )

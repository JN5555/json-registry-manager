from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .config import RegistryConfig


def load_registry(config: RegistryConfig) -> dict[str, Any]:
    path = config.registry_path
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Registry root must be an object")
    data.setdefault(config.items_key, [])
    return data


def save_registry(config: RegistryConfig, data: dict[str, Any]) -> None:
    if config.metadata_date_field:
        data[config.metadata_date_field] = date.today().isoformat()
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    config.registry_path.write_text(text, encoding="utf-8")


def entries(config: RegistryConfig, data: dict[str, Any]) -> list[dict[str, Any]]:
    value = data.get(config.items_key, [])
    return value if isinstance(value, list) else []


def find_entry(config: RegistryConfig, data: dict[str, Any], entry_id: str) -> dict[str, Any] | None:
    for item in entries(config, data):
        if str(item.get(config.id_field, "")) == entry_id:
            return item
    return None

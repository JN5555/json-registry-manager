from __future__ import annotations

import re
from urllib.parse import urlsplit
from dataclasses import dataclass
from typing import Any

from .config import RegistryConfig, FieldConfig

HOST_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")


@dataclass
class ValidationIssue:
    entry: str
    field: str
    code: str
    value: Any = None


def normalize_hostname(value: str) -> str:
    """Normalize a hostname already stored in a registry.

    This intentionally does not strip URL paths. Registry validation should still
    reject values such as ``example.com/login`` when they were written to JSON
    manually.
    """
    return value.strip().lower().removeprefix("www.").rstrip(".")


def normalize_hostname_input(value: str) -> str:
    """Turn common user input (hostname or URL) into a hostname.

    Interactive users frequently paste ``https://example.com/login`` or
    ``example.com/login`` into a field that stores hostnames. Accepting that input
    is friendly, while the persisted registry remains strict and contains only
    the hostname.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw if "://" in raw else f"//{raw}")
        if parsed.hostname:
            return normalize_hostname(parsed.hostname)
    except ValueError:
        pass
    return normalize_hostname(raw)


def validate_hostname(value: str) -> bool:
    return bool(HOST_RE.fullmatch(normalize_hostname(value)))


def validate_slug(value: str) -> bool:
    return bool(SLUG_RE.fullmatch(value.strip().lower()))


def _type_ok(field: FieldConfig, value: Any) -> bool:
    if field.type in {"string", "slug", "choice"}:
        return isinstance(value, str)
    if field.type == "list":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if field.type == "boolean":
        return isinstance(value, bool)
    if field.type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate_registry(config: RegistryConfig, data: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(data, dict):
        return [ValidationIssue("<root>", "", "root")]
    items = data.get(config.items_key)
    if not isinstance(items, list):
        return [ValidationIssue("<root>", config.items_key, "items")]

    ids: set[str] = set()
    unique_values: dict[str, set[str]] = {f.name: set() for f in config.fields if f.unique}

    for index, item in enumerate(items):
        entry_name = str(item.get(config.id_field) or f"#{index + 1}") if isinstance(item, dict) else f"#{index + 1}"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(entry_name, "", "type", "object"))
            continue
        for field in config.fields:
            present = field.name in item
            value = item.get(field.name)
            if field.required and (not present or value in (None, "", [])):
                issues.append(ValidationIssue(entry_name, field.name, "required"))
                continue
            if not present:
                continue
            if not _type_ok(field, value):
                issues.append(ValidationIssue(entry_name, field.name, "type", field.type))
                continue
            values = value if field.type == "list" else [value]
            if field.type == "choice" and value not in field.values:
                issues.append(ValidationIssue(entry_name, field.name, "choice", value))
            if field.type == "slug" and isinstance(value, str) and not validate_slug(value):
                issues.append(ValidationIssue(entry_name, field.name, "slug", value))
            if field.validator == "hostname":
                for v in values:
                    if not validate_hostname(v):
                        issues.append(ValidationIssue(entry_name, field.name, "hostname", v))
            if field.unique:
                for v in values:
                    key = str(v).lower()
                    if key in unique_values[field.name]:
                        issues.append(ValidationIssue(entry_name, field.name, "duplicate_value", v))
                    else:
                        unique_values[field.name].add(key)

        entry_id = str(item.get(config.id_field, ""))
        if entry_id:
            if entry_id in ids:
                issues.append(ValidationIssue(entry_name, config.id_field, "duplicate_id", entry_id))
            ids.add(entry_id)
    return issues

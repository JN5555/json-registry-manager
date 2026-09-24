from __future__ import annotations

import re
import unicodedata
from typing import Any

from .config import RegistryConfig, FieldConfig
from .validators import normalize_hostname
from .prompts import Choice, select, text


def slugify(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", ascii_text.lower()).strip("-_")
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]


def _label(field: FieldConfig, lang: str) -> str:
    return field.label_for(lang)


def _ask_list(field: FieldConfig, current: list[str] | None, lang: str) -> list[str]:
    existing = current or []
    default = ", ".join(existing)
    answer = text(f"{_label(field, lang)} (comma separated)", default=default)
    if answer is None:
        return existing
    values = [v.strip() for v in answer.split(",") if v.strip()]
    if field.validator == "hostname":
        values = [normalize_hostname(v) for v in values]
    return list(dict.fromkeys(values))


def ask_field(field: FieldConfig, lang: str, current: Any = None, auto_id_from: str | None = None) -> Any:
    label = _label(field, lang)
    if field.type == "choice":
        choices = []
        for raw in field.values:
            labels = field.value_labels.get(raw, raw)
            if isinstance(labels, dict):
                display = labels.get(lang) or labels.get("en") or raw
            else:
                display = str(labels)
            choices.append(Choice(display, raw))
        answer = select(label, choices=choices, default=current if current in field.values else None)
        return current if answer is None else answer
    if field.type == "list":
        return _ask_list(field, current if isinstance(current, list) else [], lang)
    if field.type == "boolean":
        from .prompts import confirm
        answer = confirm(label, default=bool(current))
        return bool(current) if answer is None else answer
    if field.type == "integer":
        answer = text(label, default="" if current is None else str(current))
        if answer is None or answer == "":
            return current
        return int(answer)

    default = "" if current is None else str(current)
    if field.type == "slug" and not default and auto_id_from:
        default = slugify(auto_id_from)
    answer = text(label, default=default)
    if answer is None:
        return current
    answer = answer.strip()
    if field.type == "slug":
        return slugify(answer)
    return answer


def create_entry(config: RegistryConfig, lang: str) -> dict[str, Any] | None:
    entry: dict[str, Any] = {}
    display_value: str | None = None
    ordered = list(config.fields)
    display_field = config.field(config.display_field)
    id_field = config.field(config.id_field)
    if display_field and display_field in ordered:
        ordered.remove(display_field)
        ordered.insert(0, display_field)
    if id_field and id_field in ordered:
        ordered.remove(id_field)
        ordered.insert(1 if display_field else 0, id_field)

    for field in ordered:
        value = ask_field(field, lang, field.default, auto_id_from=display_value if field.name == config.id_field else None)
        if field.name == config.display_field and isinstance(value, str):
            display_value = value
        if value not in (None, "", []):
            entry[field.name] = value
    return entry


def edit_entry(config: RegistryConfig, lang: str, entry: dict[str, Any]) -> dict[str, Any]:
    updated = dict(entry)
    for field in config.fields:
        current = updated.get(field.name)
        value = ask_field(field, lang, current)
        if value in (None, "", []) and not field.required:
            updated.pop(field.name, None)
        else:
            updated[field.name] = value
    return updated

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import RegistryConfig
from .i18n import Translator
from .validators import ValidationIssue

console = Console()


def header(config: RegistryConfig, data: dict[str, Any], tr: Translator) -> None:
    count = len(data.get(config.items_key, [])) if isinstance(data.get(config.items_key), list) else 0
    body = f"[bold]{tr.t('app.project')}:[/bold] {config.name}\n[bold]{tr.t('app.file')}:[/bold] {config.registry_path.name}\n[bold]{tr.t('app.entries')}:[/bold] {count}"
    console.print(Panel(body, title="JSON Registry Manager", subtitle=tr.t("app.subtitle")))


def _choice_label(config: RegistryConfig, field_name: str, value: Any, lang: str) -> str:
    field = config.field(field_name)
    if not field or field.type != "choice":
        return str(value)
    labels = field.value_labels.get(str(value), str(value))
    if isinstance(labels, dict):
        return str(labels.get(lang) or labels.get("en") or value)
    return str(labels)


def _column_count(width: int) -> int:
    if width < 76:
        return 1
    if width < 126:
        return 2
    return 3


def _summary(config: RegistryConfig, item: dict[str, Any], tr: Translator) -> Text:
    entry_id = str(item.get(config.id_field, ""))
    display = str(item.get(config.display_field, entry_id))
    text = Text()
    text.append(display or entry_id, style="bold")
    if entry_id and entry_id != display:
        text.append(f"\n[{entry_id}]", style="dim")
    category = item.get("category") if config.field("category") else None
    if category not in (None, ""):
        text.append("\n")
        text.append(_choice_label(config, "category", category, tr.language), style="cyan")
    return text


def entry_grid(config: RegistryConfig, items: list[dict[str, Any]], tr: Translator) -> None:
    """Compact adaptive registry overview: 1–3 columns depending on terminal width."""
    if not items:
        console.print(tr.t("result.no_matches"))
        return
    columns = _column_count(console.width)
    table = Table.grid(expand=True, padding=(0, 2))
    for _ in range(columns):
        table.add_column(ratio=1)
    for start in range(0, len(items), columns):
        chunk = items[start:start + columns]
        cells = [_summary(config, item, tr) for item in chunk]
        cells.extend(Text("") for _ in range(columns - len(cells)))
        table.add_row(*cells)
        if start + columns < len(items):
            table.add_row(*[Text("─" * 8, style="dim") for _ in range(columns)])
    console.print(table)
    console.print(f"[dim]{tr.t('result.shown_entries', count=len(items))}[/dim]")


def entry_table(config: RegistryConfig, items: list[dict[str, Any]], tr: Translator) -> None:
    """Backward-compatible alias; compact grid is easier to scan for long registries."""
    entry_grid(config, items, tr)


def entry_detail(config: RegistryConfig, item: dict[str, Any], tr: Translator) -> None:
    title = str(item.get(config.display_field) or item.get(config.id_field) or tr.t("action.detail"))
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold", no_wrap=True)
    table.add_column()
    known = set()
    for field in config.fields:
        if field.name not in item:
            continue
        known.add(field.name)
        value = item.get(field.name)
        if isinstance(value, list):
            rendered = ", ".join(str(v) for v in value)
        elif field.type == "choice":
            rendered = _choice_label(config, field.name, value, tr.language)
        else:
            rendered = str(value)
        table.add_row(field.label_for(tr.language), rendered)
    for key, value in item.items():
        if key in known:
            continue
        rendered = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
        table.add_row(str(key), rendered)
    console.print(Panel(table, title=title))


def print_issues(issues: list[ValidationIssue], tr: Translator) -> None:
    if not issues:
        console.print(f"[green]✓ {tr.t('result.valid')}[/green]")
        return
    console.print(f"[red]✗ {tr.t('result.invalid')}[/red]")
    for issue in issues:
        if issue.code == "required":
            msg = tr.t("validation.required", field=issue.field)
        elif issue.code == "type":
            msg = tr.t("validation.type", field=issue.field, expected=issue.value)
        elif issue.code == "choice":
            msg = tr.t("validation.choice", field=issue.field, value=issue.value)
        elif issue.code == "hostname":
            msg = tr.t("validation.hostname", field=issue.field, value=issue.value)
        elif issue.code == "slug":
            msg = tr.t("validation.slug", field=issue.field, value=issue.value)
        elif issue.code == "duplicate_id":
            msg = tr.t("validation.duplicate_id", value=issue.value)
        elif issue.code == "duplicate_value":
            msg = tr.t("validation.duplicate_value", field=issue.field, value=issue.value)
        elif issue.code == "items":
            msg = tr.t("validation.items", key=issue.field)
        elif issue.code == "root":
            msg = tr.t("validation.root")
        else:
            msg = issue.code
        console.print(Text(f"  • {issue.entry}: {msg}"))

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


def entry_table(config: RegistryConfig, items: list[dict[str, Any]], tr: Translator) -> None:
    table = Table(show_lines=False)
    table.add_column(tr.t("table.id"), style="bold")
    table.add_column(tr.t("table.name"))
    category_field = config.field("category")
    if category_field:
        table.add_column(tr.t("table.category"))
    for item in items:
        row = [str(item.get(config.id_field, "")), str(item.get(config.display_field, ""))]
        if category_field:
            row.append(str(item.get("category", "")))
        table.add_row(*row)
    console.print(table)


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

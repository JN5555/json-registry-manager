from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from . import __version__
from .config import RegistryConfig, load_config
from .editor import create_entry, edit_entry
from .gitops import GitError, commit as git_commit, diff as git_diff, is_repo, push as git_push, status_short
from .i18n import Translator, resolve_language, write_language_setting
from .initializer import init_project
from .registry import entries, find_entry, load_registry, save_registry
from .prompts import Choice, autocomplete_select, confirm, press_any_key_to_continue, select, text
from .render import entry_detail, entry_grid, entry_table, header, print_issues
from .validators import validate_registry

console = Console()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jrm", description="JSON Registry Manager")
    parser.add_argument("--config", default="registry.yaml", help="Path to registry YAML configuration")
    parser.add_argument("--lang", choices=["auto", "en", "cs"], help="UI language for this run")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialize registry.yaml for this project")
    p_init.add_argument("--force", action="store_true", help="Overwrite generated files when safe")

    sub.add_parser("list", help="List registry entries")
    sub.add_parser("validate", help="Validate registry")

    p_search = sub.add_parser("search", help="Search registry")
    p_search.add_argument("text")

    sub.add_parser("add", help="Add an entry interactively")

    p_edit = sub.add_parser("edit", help="Edit an entry interactively")
    p_edit.add_argument("id")

    p_remove = sub.add_parser("remove", help="Remove an entry")
    p_remove.add_argument("id")
    p_remove.add_argument("--yes", action="store_true")

    sub.add_parser("diff", help="Show Git diff")

    p_commit = sub.add_parser("commit", help="Create a Git commit")
    p_commit.add_argument("message", nargs="?")

    sub.add_parser("push", help="Push current Git branch")

    p_language = sub.add_parser("language", help="Set persistent UI language")
    p_language.add_argument("value", nargs="?", choices=["auto", "en", "cs"])

    return parser


def _load(args: argparse.Namespace) -> tuple[RegistryConfig, dict[str, Any], Translator]:
    lang = resolve_language(args.lang)
    tr = Translator(lang)
    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        console.print(f"[red]{tr.t('error.config_missing', path=exc.args[0])}[/red]")
        raise SystemExit(2)
    try:
        data = load_registry(cfg)
    except FileNotFoundError as exc:
        console.print(f"[red]{tr.t('error.registry_missing', path=exc.args[0])}[/red]")
        raise SystemExit(2)
    except (json.JSONDecodeError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(2)
    return cfg, data, tr


def _matches(config: RegistryConfig, data: dict[str, Any], text: str) -> list[dict[str, Any]]:
    needle = text.casefold().strip()
    results: list[dict[str, Any]] = []
    for item in entries(config, data):
        haystack_parts: list[str] = []
        for value in item.values():
            if isinstance(value, list):
                haystack_parts.extend(str(v) for v in value)
            else:
                haystack_parts.append(str(value))
        if needle in " ".join(haystack_parts).casefold():
            results.append(item)
    return results


def _validate_and_print(config: RegistryConfig, data: dict[str, Any], tr: Translator) -> bool:
    issues = validate_registry(config, data)
    print_issues(issues, tr)
    return not issues


def _save_if_valid(config: RegistryConfig, data: dict[str, Any], tr: Translator) -> bool:
    issues = validate_registry(config, data)
    if issues:
        print_issues(issues, tr)
        return False
    save_registry(config, data)
    console.print(f"[green]✓ {tr.t('result.saved')}[/green]")
    return True


def _candidate_data(config: RegistryConfig, data: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = dict(data)
    candidate[config.items_key] = items
    return candidate


def cmd_add(config: RegistryConfig, data: dict[str, Any], tr: Translator) -> int:
    item = create_entry(config, tr.language)
    if not item:
        return 1

    while True:
        candidate_items = [*entries(config, data), item]
        issues = validate_registry(config, _candidate_data(config, data, candidate_items))
        if not issues:
            entries(config, data).append(item)
            save_registry(config, data)
            console.print(f"[green]✓ {tr.t('result.saved')}[/green]")
            return 0

        print_issues(issues, tr)
        if not confirm(tr.t("prompt.fix_entry"), default=True):
            console.print(f"[yellow]{tr.t('result.cancelled')}[/yellow]")
            return 1
        # Keep everything the user already entered. Pressing Enter on a field keeps
        # its current value, so only the invalid field needs to be corrected.
        item = edit_entry(config, tr.language, item)


def cmd_edit(config: RegistryConfig, data: dict[str, Any], tr: Translator, entry_id: str) -> int:
    item = find_entry(config, data, entry_id)
    if not item:
        console.print(f"[red]{tr.t('error.not_found', id=entry_id)}[/red]")
        return 1
    index = entries(config, data).index(item)
    updated = edit_entry(config, tr.language, item)

    while True:
        candidate_items = list(entries(config, data))
        candidate_items[index] = updated
        issues = validate_registry(config, _candidate_data(config, data, candidate_items))
        if not issues:
            entries(config, data)[index] = updated
            save_registry(config, data)
            console.print(f"[green]✓ {tr.t('result.saved')}[/green]")
            return 0

        print_issues(issues, tr)
        if not confirm(tr.t("prompt.fix_entry"), default=True):
            console.print(f"[yellow]{tr.t('result.cancelled')}[/yellow]")
            return 1
        updated = edit_entry(config, tr.language, updated)


def cmd_remove(config: RegistryConfig, data: dict[str, Any], tr: Translator, entry_id: str, assume_yes: bool = False) -> int:
    item = find_entry(config, data, entry_id)
    if not item:
        console.print(f"[red]{tr.t('error.not_found', id=entry_id)}[/red]")
        return 1
    name = item.get(config.display_field) or entry_id
    if not assume_yes:
        confirmed = confirm(tr.t("prompt.confirm_remove", name=name), default=False)
        if not confirmed:
            return 1
    entries(config, data).remove(item)
    save_registry(config, data)
    console.print(f"[green]✓ {tr.t('result.removed')}[/green]")
    return 0


def _ensure_git(config: RegistryConfig, tr: Translator) -> Path | None:
    cwd = config.base_dir
    if not is_repo(cwd):
        console.print(f"[red]{tr.t('error.git_missing')}[/red]")
        return None
    return cwd


def cmd_diff(config: RegistryConfig, tr: Translator) -> int:
    cwd = _ensure_git(config, tr)
    if not cwd:
        return 1
    try:
        status = status_short(cwd)
        if not status:
            console.print(f"[green]{tr.t('result.clean')}[/green]")
            return 0
        console.print(Panel(status, title="git status --short"))
        delta = git_diff(cwd)
        if delta:
            console.print(Syntax(delta, "diff", line_numbers=False, word_wrap=False))
        return 0
    except GitError as exc:
        console.print(f"[red]{tr.t('error.git_command', message=exc)}[/red]")
        return 1


def cmd_commit(config: RegistryConfig, tr: Translator, message: str | None) -> int:
    cwd = _ensure_git(config, tr)
    if not cwd:
        return 1
    message = message or text(tr.t("prompt.commit"))
    if not message:
        return 1
    try:
        output = git_commit(cwd, message, [config.registry_path.relative_to(cwd)])
        console.print(f"[green]✓ {tr.t('result.committed')}[/green]")
        if output:
            console.print(output)
        return 0
    except GitError as exc:
        console.print(f"[red]{tr.t('error.git_command', message=exc)}[/red]")
        return 1


def cmd_push(config: RegistryConfig, tr: Translator) -> int:
    cwd = _ensure_git(config, tr)
    if not cwd:
        return 1
    try:
        output = git_push(cwd)
        console.print(f"[green]✓ {tr.t('result.pushed')}[/green]")
        if output:
            console.print(output)
        return 0
    except GitError as exc:
        console.print(f"[red]{tr.t('error.git_command', message=exc)}[/red]")
        return 1


def _entry_choices(config: RegistryConfig, items: list[dict[str, Any]]) -> list[Choice]:
    choices: list[Choice] = []
    for item in items:
        entry_id = str(item.get(config.id_field, ""))
        display = str(item.get(config.display_field, entry_id))
        category = str(item.get("category", ""))
        suffix = f" · {category}" if category else ""
        choices.append(Choice(f"{display}  [{entry_id}]{suffix}", entry_id))
    return choices


def choose_entry(config: RegistryConfig, data: dict[str, Any], tr: Translator, items: list[dict[str, Any]] | None = None) -> str | None:
    items = list(items if items is not None else entries(config, data))
    if not items:
        return None
    choices = _entry_choices(config, items)
    if len(choices) > 18:
        return autocomplete_select(tr.t("prompt.choose_entry_filter"), choices)
    return select(tr.t("prompt.choose_entry"), choices=choices)


def _search_actions(config: RegistryConfig, data: dict[str, Any], tr: Translator, found: list[dict[str, Any]]) -> None:
    if not found:
        console.print(tr.t("result.no_matches"))
        return
    entry_grid(config, found, tr)
    console.print(f"[bold]{tr.t('result.search_matches', count=len(found))}[/bold]")
    entry_id = choose_entry(config, data, tr, found)
    if not entry_id:
        return
    while True:
        item = find_entry(config, data, entry_id)
        if not item:
            return
        action = select(tr.t("prompt.result_action"), [
            Choice(tr.t("action.detail"), "detail"),
            Choice(tr.t("action.edit"), "edit"),
            Choice(tr.t("action.remove"), "remove"),
            Choice(tr.t("action.back"), "back"),
        ])
        if not action or action == "back":
            return
        if action == "detail":
            entry_detail(config, item, tr)
            press_any_key_to_continue(tr.t("prompt.continue"))
        elif action == "edit":
            cmd_edit(config, data, tr, entry_id)
            return
        elif action == "remove":
            cmd_remove(config, data, tr, entry_id)
            return


def settings_menu(tr: Translator) -> None:
    choices = [
        Choice(tr.t("settings.language.auto"), "auto"),
        Choice(tr.t("settings.language.en"), "en"),
        Choice(tr.t("settings.language.cs"), "cs"),
    ]
    value = select(tr.t("settings.language"), choices=choices)
    if value:
        write_language_setting(value)
        console.print(f"[green]✓ {tr.t('settings.saved')}[/green]")


def interactive(config: RegistryConfig, data: dict[str, Any], tr: Translator) -> int:
    while True:
        console.clear()
        header(config, data, tr)
        action = select("", [
            Choice(tr.t("menu.add"), "add"),
            Choice(tr.t("menu.list"), "list"),
            Choice(tr.t("menu.edit"), "edit"),
            Choice(tr.t("menu.remove"), "remove"),
            Choice(tr.t("menu.search"), "search"),
            Choice(tr.t("menu.validate"), "validate"),
            Choice(tr.t("menu.diff"), "diff"),
            Choice(tr.t("menu.commit"), "commit"),
            Choice(tr.t("menu.push"), "push"),
            Choice(tr.t("menu.settings"), "settings"),
            Choice(tr.t("menu.exit"), "exit"),
        ])
        if not action or action == "exit":
            return 0
        if action == "add":
            cmd_add(config, data, tr)
        elif action == "list":
            entry_grid(config, entries(config, data), tr)
        elif action == "edit":
            entry_id = choose_entry(config, data, tr)
            if entry_id:
                cmd_edit(config, data, tr, entry_id)
        elif action == "remove":
            entry_id = choose_entry(config, data, tr)
            if entry_id:
                cmd_remove(config, data, tr, entry_id)
        elif action == "search":
            query = text(tr.t("prompt.search")) or ""
            found = _matches(config, data, query)
            _search_actions(config, data, tr, found)
        elif action == "validate":
            _validate_and_print(config, data, tr)
        elif action == "diff":
            cmd_diff(config, tr)
        elif action == "commit":
            cmd_commit(config, tr, None)
        elif action == "push":
            cmd_push(config, tr)
        elif action == "settings":
            settings_menu(tr)
        press_any_key_to_continue()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "init":
        tr = Translator(resolve_language(args.lang))
        return init_project(args.config, tr, force=args.force)

    if args.command == "language":
        current_tr = Translator(resolve_language(args.lang))
        value = args.value
        if not value:
            choices = [
                Choice(current_tr.t("settings.language.auto"), "auto"),
                Choice(current_tr.t("settings.language.en"), "en"),
                Choice(current_tr.t("settings.language.cs"), "cs"),
            ]
            value = select(current_tr.t("settings.language"), choices=choices)
        if value:
            write_language_setting(value)
            console.print(f"[green]✓ {current_tr.t('settings.saved')}[/green]")
            return 0
        return 1

    # Friendly first-run behavior: `jrm` in a project without registry.yaml can
    # create the configuration immediately instead of failing with a dead end.
    config_path = Path(args.config).expanduser().resolve()
    if not args.command and not config_path.exists():
        tr = Translator(resolve_language(args.lang))
        console.print(f"[yellow]{tr.t('error.config_missing', path=config_path)}[/yellow]")
        if confirm(tr.t("init.offer"), default=True):
            if init_project(config_path, tr) != 0:
                return 1
        else:
            return 1

    config, data, tr = _load(args)

    if not args.command:
        return interactive(config, data, tr)
    if args.command == "list":
        entry_grid(config, entries(config, data), tr)
        return 0
    if args.command == "validate":
        return 0 if _validate_and_print(config, data, tr) else 1
    if args.command == "search":
        found = _matches(config, data, args.text)
        if not found:
            console.print(tr.t("result.no_matches"))
            return 1
        entry_grid(config, found, tr)
        return 0
    if args.command == "add":
        return cmd_add(config, data, tr)
    if args.command == "edit":
        return cmd_edit(config, data, tr, args.id)
    if args.command == "remove":
        return cmd_remove(config, data, tr, args.id, args.yes)
    if args.command == "diff":
        return cmd_diff(config, tr)
    if args.command == "commit":
        return cmd_commit(config, tr, args.message)
    if args.command == "push":
        return cmd_push(config, tr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

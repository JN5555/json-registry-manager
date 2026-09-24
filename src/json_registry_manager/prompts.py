from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import questionary as _q

    JRM_STYLE = _q.Style([
        ("qmark", "fg:#00afff bold"),
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#87d787 bold"),
        ("pointer", "fg:#00afff bold"),

        # Běžné výběrové menu
        ("highlighted", "fg:#ffffff bg:#005f87 bold"),
        ("selected", "fg:#87d787"),

        # AUTOCOMPLETE – rozbalovací výsledky při filtrování
        ("completion-menu.completion", "fg:#e6e6e6 bg:#202428"),
        ("completion-menu.completion.current", "fg:#ffffff bg:#005f87 bold"),

        # Pokud by autocomplete zobrazoval metadata
        ("completion-menu.meta.completion", "fg:#bcbcbc bg:#202428"),
        ("completion-menu.meta.completion.current", "fg:#ffffff bg:#005f87"),

        # Posuvník autocomplete nabídky
        ("scrollbar.background", "bg:#303438"),
        ("scrollbar.button", "bg:#70757a"),

        ("separator", "fg:#808080"),
        ("instruction", "fg:#a0a0a0"),
        ("text", "fg:#ffffff"),
        ("disabled", "fg:#707070 italic"),
    ])

except Exception:  # pragma: no cover - fallback for minimal environments
    _q = None
    JRM_STYLE = None


@dataclass
class Choice:
    title: str
    value: Any


def text(message: str, default: str = "") -> str | None:
    if _q:
        return _q.text(
            message,
            default=default,
            style=JRM_STYLE,
        ).ask()

    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ")
    return value if value else default


def confirm(message: str, default: bool = False) -> bool | None:
    if _q:
        return _q.confirm(
            message,
            default=default,
            style=JRM_STYLE,
        ).ask()

    hint = "Y/n" if default else "y/N"
    value = input(f"{message} [{hint}]: ").strip().lower()

    if not value:
        return default

    return value in {"y", "yes", "a", "ano"}


def select(
    message: str,
    choices: list[Choice],
    default: Any = None,
) -> Any:
    if _q:
        qchoices = [
            _q.Choice(c.title, value=c.value)
            for c in choices
        ]

        return _q.select(
            message,
            choices=qchoices,
            default=default,
            style=JRM_STYLE,
        ).ask()

    if message:
        print(message)

    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice.title}")

    while True:
        raw = input("> ").strip()

        if not raw and default is not None:
            return default

        try:
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1].value
        except ValueError:
            pass

        print("Invalid choice.")


def autocomplete_select(
    message: str,
    choices: list[Choice],
) -> Any:
    """Select from a large list with type-to-filter support."""

    if _q:
        mapping = {
            c.title: c.value
            for c in choices
        }

        answer = _q.autocomplete(
            message,
            choices=list(mapping),
            match_middle=True,
            ignore_case=True,
            style=JRM_STYLE,
        ).ask()

        return mapping.get(answer) if answer is not None else None

    return select(
        message,
        choices=choices,
    )


def press_any_key_to_continue(
    message: str = "Press Enter to continue...",
) -> None:
    if _q:
        _q.press_any_key_to_continue(
            message,
            style=JRM_STYLE,
        ).ask()
    else:
        input(message)

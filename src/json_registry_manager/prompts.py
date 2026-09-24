from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import questionary as _q
except Exception:  # pragma: no cover - fallback for minimal environments
    _q = None


@dataclass
class Choice:
    title: str
    value: Any


def text(message: str, default: str = "") -> str | None:
    if _q:
        return _q.text(message, default=default).ask()
    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ")
    return value if value else default


def confirm(message: str, default: bool = False) -> bool | None:
    if _q:
        return _q.confirm(message, default=default).ask()
    hint = "Y/n" if default else "y/N"
    value = input(f"{message} [{hint}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "a", "ano"}


def select(message: str, choices: list[Choice], default: Any = None) -> Any:
    if _q:
        qchoices = [_q.Choice(c.title, value=c.value) for c in choices]
        return _q.select(message, choices=qchoices, default=default).ask()
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


def press_any_key_to_continue(message: str = "Press Enter to continue...") -> None:
    if _q:
        _q.press_any_key_to_continue(message).ask()
    else:
        input(message)

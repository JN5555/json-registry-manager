from __future__ import annotations

import json
import locale
import os
from importlib import resources
from pathlib import Path

SUPPORTED = {"en", "cs"}


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    return Path(base) / "json-registry-manager" if base else Path.home() / ".config" / "json-registry-manager"


def settings_path() -> Path:
    return config_dir() / "config.toml"


def read_language_setting() -> str:
    path = settings_path()
    if not path.exists():
        return "auto"
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("language") and "=" in line:
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value if value in SUPPORTED | {"auto"} else "auto"
    except OSError:
        pass
    return "auto"


def write_language_setting(value: str) -> None:
    if value not in SUPPORTED | {"auto"}:
        raise ValueError(value)
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'language = "{value}"\n', encoding="utf-8")


def system_language() -> str:
    candidates = [
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
    ]
    try:
        loc = locale.getlocale()[0]
        candidates.append(loc)
    except Exception:
        pass
    for value in candidates:
        if not value:
            continue
        normalized = value.lower().replace("-", "_")
        if normalized.startswith("cs"):
            return "cs"
    return "en"


def resolve_language(cli_value: str | None = None) -> str:
    choice = cli_value or read_language_setting()
    if choice == "auto":
        return system_language()
    return choice if choice in SUPPORTED else "en"


class Translator:
    def __init__(self, language: str):
        self.language = language if language in SUPPORTED else "en"
        self._messages = self._load(self.language)
        self._fallback = self._load("en") if self.language != "en" else self._messages

    @staticmethod
    def _load(language: str) -> dict[str, str]:
        package = resources.files("json_registry_manager").joinpath("i18n", f"{language}.json")
        return json.loads(package.read_text(encoding="utf-8"))

    def t(self, key: str, **kwargs) -> str:
        value = self._messages.get(key, self._fallback.get(key, key))
        try:
            return value.format(**kwargs)
        except Exception:
            return value

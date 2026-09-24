from json_registry_manager.i18n import Translator, system_language


def test_czech_translation():
    tr = Translator("cs")
    assert tr.t("menu.add") == "Přidat položku"


def test_english_translation():
    tr = Translator("en")
    assert tr.t("menu.add") == "Add entry"


def test_system_language_czech(monkeypatch):
    monkeypatch.setenv("LC_ALL", "cs_CZ.UTF-8")
    assert system_language() == "cs"

from pathlib import Path

from json_registry_manager.config import load_config
from json_registry_manager.registry import load_registry
from json_registry_manager.validators import normalize_hostname_input, validate_hostname, validate_registry


def example_dir() -> Path:
    return Path(__file__).parents[1] / "examples" / "phishing-domain-guard"


def test_hostname_validation():
    assert validate_hostname("airbank.cz")
    assert validate_hostname("ib.airbank.cz")
    assert not validate_hostname("https://airbank.cz")
    assert not validate_hostname("airbank.cz/login")


def test_hostname_input_normalization():
    assert normalize_hostname_input("online.csob-penze.cz/login") == "online.csob-penze.cz"
    assert normalize_hostname_input("https://online.csob-penze.cz/login?next=1") == "online.csob-penze.cz"
    assert normalize_hostname_input("www.example.cz") == "example.cz"


def test_example_registry_is_valid():
    cfg = load_config(example_dir() / "registry.yaml")
    data = load_registry(cfg)
    assert validate_registry(cfg, data) == []


def test_duplicate_id_is_reported():
    cfg = load_config(example_dir() / "registry.yaml")
    data = load_registry(cfg)
    data["entities"].append(dict(data["entities"][0]))
    codes = [issue.code for issue in validate_registry(cfg, data)]
    assert "duplicate_id" in codes

import json
from pathlib import Path

import yaml

from json_registry_manager.initializer import discover_registry_lists, infer_fields, write_project_files


def test_discover_registry_lists():
    data = {"meta": {}, "items": [{"id": "a"}], "other": [1, 2, 3], "empty": []}
    assert discover_registry_lists(data) == ["items", "empty"]


def test_infer_existing_fields():
    items = [
        {"id": "one", "name": "One", "urls": ["example.com"], "enabled": True},
        {"id": "two", "name": "Two", "urls": ["example.org"], "enabled": False},
    ]
    fields = infer_fields(items)
    assert fields["id"]["type"] == "slug"
    assert fields["id"]["unique"] is True
    assert fields["name"]["required"] is True
    assert fields["urls"]["type"] == "list"
    assert fields["enabled"]["type"] == "boolean"


def test_write_project_files(tmp_path: Path):
    config_path = tmp_path / "registry.yaml"
    registry_path = tmp_path / "urls.json"
    config = {
        "name": "URLs",
        "file": "urls.json",
        "items_key": "items",
        "id_field": "id",
        "display_field": "name",
        "metadata_date_field": None,
        "fields": {"id": {"type": "slug", "required": True}},
    }
    registry = {"items": []}
    write_project_files(config_path, registry_path, config, registry)
    parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert parsed["file"] == "urls.json"
    assert json.loads(registry_path.read_text(encoding="utf-8")) == registry

from json_registry_manager.editor import slugify


def test_slugify_czech():
    assert slugify("Česká spořitelna / George") == "ceska-sporitelna-george"


def test_field_help_and_example_are_localized(tmp_path):
    from json_registry_manager.config import load_config

    cfg_file = tmp_path / "registry.yaml"
    cfg_file.write_text(
        """
name: Demo
file: data.json
fields:
  domain:
    type: string
    help:
      en: Main website
      cs: Hlavní web
    example:
      en: example.com
      cs: priklad.cz
""",
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    field = cfg.field("domain")
    assert field is not None
    assert field.help_for("cs") == "Hlavní web"
    assert field.help_for("en") == "Main website"
    assert field.example_for("cs") == "priklad.cz"

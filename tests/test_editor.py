from json_registry_manager.editor import slugify


def test_slugify_czech():
    assert slugify("Česká spořitelna / George") == "ceska-sporitelna-george"

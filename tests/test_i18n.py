"""Runtime-message catalog tests: coverage, placeholders and markers."""

import ast
import glob
import re

from core import i18n
from core.i18n import _CATALOG, banner_words, tr


def _source_tr_keys() -> set[str]:
    """Every literal key passed to tr() anywhere in the project sources.

    Implicit string concatenation is merged by the parser, so multi-line
    keys are collected correctly.
    """
    keys: set[str] = set()
    for path in glob.glob("**/*.py", recursive=True):
        if path.startswith("tests/"):
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "tr"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                keys.add(node.args[0].value)
    return keys


def test_catalogs_share_the_same_keyset():
    assert set(_CATALOG["ru"]) == set(_CATALOG["uk"])


def test_every_tr_key_in_source_is_translated():
    keys = _source_tr_keys()
    assert keys, "no tr() calls found — the scanner is broken"
    for lang, catalog in _CATALOG.items():
        missing = keys - set(catalog)
        assert not missing, f"missing {lang} translations: {sorted(missing)}"


def test_placeholders_match_between_key_and_translations():
    placeholder = re.compile(r"\{(\w+)\}")
    for lang, catalog in _CATALOG.items():
        for key, value in catalog.items():
            assert set(placeholder.findall(key)) == set(placeholder.findall(value)), (
                f"{lang}: placeholder mismatch in {key!r}"
            )


def test_structural_markers_preserved_in_translations():
    for lang, catalog in _CATALOG.items():
        for key, value in catalog.items():
            if key.startswith("|||"):
                assert value.startswith("|||") and value.endswith("|||"), (lang, key)
            if key.startswith("<<<"):
                assert value.startswith("<<<") and value.endswith(">>>"), (lang, key)
            if key.startswith("---"):
                assert value.startswith("---") and value.endswith("---"), (lang, key)


def test_tr_translates_interpolates_and_falls_back():
    try:
        i18n.set_language("ru")
        assert tr("New order") == "Новый заказ"
        assert (
            tr("File {path} not found.", path="orders.txt")
            == "Файл orders.txt не найден."
        )
        assert tr("No such key {x}", x=1) == "No such key 1"
        i18n.set_language("uk")
        assert tr("New order") == "Нове замовлення"
    finally:
        i18n.set_language("en")


def test_set_language_ignores_unknown_codes():
    try:
        i18n.set_language("de")
        assert i18n.get_language() == "en"
    finally:
        i18n.set_language("en")


def test_banner_parses_in_every_language():
    from ui.log_format import parse_entry

    assert set(banner_words()) == {"New order", "Новый заказ", "Нове замовлення"}
    for word in banner_words():
        entry = parse_entry(f"----- {word} Etsy -----")
        assert entry["kind"] == "banner", word
        assert entry["marketplace"] == "Etsy"

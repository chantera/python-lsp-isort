import os
from dataclasses import asdict

import isort
import pytest

from pylsp_isort import plugin


def _read_content(filename):
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as f:
        return f.read()


@pytest.mark.parametrize(
    ("text", "settings", "expected"),
    [
        (
            _read_content("unformatted.py"),
            {},
            _read_content("formatted.py"),
        ),
        (
            _read_content("unformatted.py"),
            {"profile": "black"},
            _read_content("formatted_black.py"),
        ),
    ],
)
def test_run_isort(text, settings, expected):
    actual = plugin.run_isort(text, settings)
    assert actual == expected


@pytest.mark.parametrize(
    ("settings", "target_path", "expected", "check_sources"),
    [
        (
            {},
            None,
            isort.Config(),
            True,
        ),
        (
            {"profile": "black"},
            None,
            isort.Config(profile="black"),
            True,
        ),
        (
            {"profile": "black", "line_length": 120},
            None,
            isort.Config(profile="black", line_length=120),
            True,
        ),
        (
            {},
            __file__,
            isort.Config(settings_path=os.path.dirname(__file__)),
            True,
        ),
        (
            {},
            __file__,
            isort.Config(profile="black"),
            False,
        ),
        (
            {"profile": "django"},
            __file__,
            isort.Config(profile="black"),
            False,
        ),
        (
            {
                "sections": ["FUTURE", "SECTION_A", "SECTION_B"],
                "known_section_a": ["module_a"],
                "known_section_b": ["module_b"],
             },
            None,
            isort.Config(
                sections=["FUTURE", "SECTION_A", "SECTION_B"],
                known_section_a=["module_a"],
                known_section_b=["module_b"],
            ),
            True,
        ),
    ],
)
def test_isort_config(settings, target_path, expected, check_sources):
    actual = plugin.isort_config(settings, target_path)
    actual_dict = asdict(actual)
    expected_dict = asdict(expected)
    if not check_sources:
        del actual_dict["sources"]
        del expected_dict["sources"]
    assert actual_dict == expected_dict


def test_pylsp_settings(config):
    plugins = dict(config.plugin_manager.list_name_plugin())
    assert "isort" in plugins
    assert plugins["isort"] not in config.disabled_plugins
    config.update({"plugins": {"isort": {"enabled": False}}})
    assert plugins["isort"] in config.disabled_plugins
    config.update(plugin.pylsp_settings())
    assert plugins["isort"] not in config.disabled_plugins


def test_pylsp_format_document(config, unformatted_document, formatted_document):
    actual = _receive(plugin.pylsp_format_document, config, unformatted_document)

    text = _read_content(formatted_document.path)
    range = plugin.Range(
        start={"line": 0, "character": 0},
        end={"line": len(unformatted_document.lines), "character": 0},
    )
    expected = [{"range": range, "newText": text}]

    assert actual == expected


def test_pylsp_format_range(config, unformatted_document):
    range = plugin.Range(
        start={"line": 2, "character": 0},
        end={"line": 9, "character": 0},
    )
    actual = _receive(plugin.pylsp_format_range, config, unformatted_document, range)

    text = "\n".join(
        [
            "import os",
            "import sys",
            "",
            "from pylsp_isort.plugin import Range, pylsp_settings",
        ]
    )
    text += "\n"
    expected = [{"range": range, "newText": text}]

    assert actual == expected


def _receive(func, *args):
    gen = func(*args)
    next(gen)
    outcome = MockResult([])
    try:
        gen.send(outcome)
    except StopIteration:
        pass
    return outcome.get_result()


class MockResult:
    def __init__(self, result):
        self.result = result

    def get_result(self):
        return self.result

    def force_result(self, result):
        self.result = result

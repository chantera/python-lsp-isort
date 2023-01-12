import logging
import os
from pathlib import Path
from typing import Any, Dict, Generator, TypedDict

import isort
from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.workspace import Document

logger = logging.getLogger(__name__)


class Position(TypedDict):
    line: int
    character: int


class Range(TypedDict):
    start: Position
    end: Position


@hookimpl
def pylsp_settings() -> Dict[str, Any]:
    return {
        "plugins": {
            "isort": {
                "enabled": True,
            },
        },
    }


@hookimpl(hookwrapper=True)
def pylsp_format_document(config: Config, document: Document) -> Generator:
    range = Range(
        start={"line": 0, "character": 0},
        end={"line": len(document.lines), "character": 0},
    )
    outcome = yield
    _process(outcome, config, document, range)


@hookimpl(hookwrapper=True)
def pylsp_format_range(config: Config, document: Document, range: Range) -> Generator:
    outcome = yield
    _process(outcome, config, document, range)


def _process(outcome, config: Config, document: Document, range: Range):
    result = outcome.get_result()
    if result:
        text = result[0]["newText"]
        range = result[0]["range"]
    else:
        start = range["start"]["line"]
        end = range["end"]["line"]
        text = "".join(document.lines[start:end])

    config_kwargs = {}
    defined_args = set(getattr(isort.Config, "__dataclass_fields__", {}).keys())
    settings = config.plugin_settings("isort", document_path=document.path)
    for key, value in settings.items():
        if key in defined_args:
            config_kwargs[key] = value
    config_kwargs["settings_path"] = os.path.dirname(os.path.abspath(document.path))
    logger.debug("config_kwargs=%r", config_kwargs)

    new_text = isort.code(
        text, config=isort.Config(**config_kwargs), file_path=Path(document.path)
    )

    if new_text != text:
        result = [{"range": range, "newText": new_text}]
        outcome.force_result(result)

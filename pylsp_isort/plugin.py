import logging
import os
from pathlib import Path
from typing import Any, Dict, Generator, Optional, TypedDict, Union

import isort
from isort.settings import KNOWN_PREFIX
from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

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
def pylsp_format_document(
    config: Config, workspace: Workspace, document: Document
) -> Generator:
    outcome = yield
    with workspace.report_progress("format: isort"):
        _format(outcome, config, document)
    _format(outcome, config, document)


@hookimpl(hookwrapper=True)
def pylsp_format_range(config: Config, document: Document, range: Range) -> Generator:
    outcome = yield
    _format(outcome, config, document, range)


def _format(
    outcome, config: Config, document: Document, range: Optional[Range] = None
) -> None:
    result = outcome.get_result()
    if result:
        text = result[0]["newText"]
        range = result[0]["range"]
    elif range:
        text = "".join(document.lines[range["start"]["line"] : range["end"]["line"]])
    else:
        text = document.source
        range = Range(
            start={"line": 0, "character": 0},
            end={"line": len(document.lines), "character": 0},
        )

    IGNORE_KEYS = {"enabled"}
    settings = config.plugin_settings("isort", document_path=document.path)
    settings = {k: v for k, v in settings.items() if k not in IGNORE_KEYS}
    new_text = run_isort(text, settings, file_path=document.path)

    if new_text != text:
        result = [{"range": range, "newText": new_text}]
        outcome.force_result(result)


def run_isort(
    text: str,
    settings: Optional[Dict[str, Any]] = None,
    file_path: Optional[Union[str, bytes, os.PathLike]] = None,
) -> str:
    config = isort_config(settings or {}, file_path)
    file_path = Path(os.fsdecode(file_path)) if file_path else None
    return isort.code(text, config=config, file_path=file_path)


def isort_config(
    settings: Dict[str, Any],
    target_path: Optional[Union[str, bytes, os.PathLike]] = None,
) -> isort.Config:
    config_kwargs = {}
    unsupported_kwargs = {}

    defined_args = set(getattr(isort.Config, "__dataclass_fields__", {}).keys())
    for key, value in settings.items():
        if key in defined_args or key.startswith(KNOWN_PREFIX):
            config_kwargs[key] = value
        else:
            unsupported_kwargs[key] = value

    if "settings_path" in settings:
        if os.path.isfile(settings["settings_path"]):
            config_kwargs["settings_file"] = os.path.abspath(settings["settings_path"])
            config_kwargs["settings_path"] = os.path.dirname(
                config_kwargs["settings_file"]
            )
        else:
            config_kwargs["settings_path"] = os.path.abspath(settings["settings_path"])
    elif target_path:
        settings_path = os.path.abspath(target_path)
        if not os.path.isdir(settings_path):
            settings_path = os.path.dirname(settings_path)

        _, found_settings = isort.settings._find_config(settings_path)
        if found_settings:
            logger.info(
                "Found a config file: `%s`, skipping given settings.",
                found_settings["source"],
            )
            config_kwargs = {}

        config_kwargs["settings_path"] = settings_path

    logger.debug("config_kwargs=%r", config_kwargs)
    if unsupported_kwargs:
        logger.info("unsupported_kwargs=%r", unsupported_kwargs)

    return isort.Config(**config_kwargs)

import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
from pylsp import uris
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

here = Path(__file__).parent
fixtures_dir = here / "fixtures"


@pytest.fixture
def config(workspace):
    return Config(workspace.root_uri, {}, 0, {})


@pytest.fixture
def workspace(tmpdir):
    """Return a workspace."""
    ws = Workspace(uris.from_fs_path(str(tmpdir)), Mock())
    ws._config = Config(ws.root_uri, {}, 0, {})
    return ws


@pytest.fixture
def unformatted_document(workspace):
    return create_document(workspace, "unformatted.py")


@pytest.fixture
def formatted_document(workspace):
    return create_document(workspace, "formatted.py")


def create_document(workspace, name):
    template_path = fixtures_dir / name
    dest_path = Path(workspace.root_path) / name
    shutil.copy(template_path, dest_path)
    document_uri = uris.from_fs_path(str(dest_path))
    return Document(document_uri, workspace)

import os
import sys
from functools import lru_cache

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@lru_cache
def project_settings():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")
    with open(path, "rb") as f:
        data = tomllib.load(f)
        return data["tool"]["isort"]


def read_content(filename):
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as f:
        return f.read()

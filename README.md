# python-lsp-isort

[isort](https://github.com/PyCQA/isort) plugin for the [Python LSP Server](https://github.com/python-lsp/python-lsp-server).

## Install

In the same `virtualenv` as `python-lsp-server`:

```shell
pip install python-lsp-isort
```

## Configuration

The plugin follows [python-lsp-server's configuration](https://github.com/python-lsp/python-lsp-server/#configuration).
These are the valid configuration keys:

- `pylsp.plugins.isort.enabled`: boolean to enable/disable the plugin. `true` by default.
- `pylsp.plugins.isort.*`: any other key-value pair under `pylsp.plugins.isort` is passed to `isort.settings.Config`. See the [reference](https://pycqa.github.io/isort/reference/isort/settings.html#config) for details.

Note that any configurations passed to isort via `pylsp` are ignored when isort detects a config file, such as `pyproject.toml`.

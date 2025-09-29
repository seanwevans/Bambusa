"""Shim package to support running from a source checkout.

This module ensures that importing :mod:`bambusa` without installing the
package (for example by running ``python -m bambusa`` directly from the
repository root) still loads the actual implementation that lives under the
``src/`` directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PACKAGE_NAME = __name__
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_PACKAGE_PATH = _REPO_ROOT / "src" / _PACKAGE_NAME

if not _SRC_PACKAGE_PATH.exists():
    raise ModuleNotFoundError(
        f"Could not locate the '{_PACKAGE_NAME}' sources at {_SRC_PACKAGE_PATH}"
    )

_spec = importlib.util.spec_from_file_location(
    _PACKAGE_NAME,
    _SRC_PACKAGE_PATH / "__init__.py",
    submodule_search_locations=[str(_SRC_PACKAGE_PATH)],
)

if _spec is None or _spec.loader is None:
    raise ModuleNotFoundError(
        f"Unable to create a module spec for '{_PACKAGE_NAME}' from {_SRC_PACKAGE_PATH}"
    )

_module = importlib.util.module_from_spec(_spec)
sys.modules[_PACKAGE_NAME] = _module
_spec.loader.exec_module(_module)

globals().update(_module.__dict__)

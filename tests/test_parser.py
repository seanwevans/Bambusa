"""Tests for the Bambusa parser CLI."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
DATA_DIR = Path(__file__).parent / "data"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_DIR), existing]) if existing else str(SRC_DIR)
    cmd = [sys.executable, "-m", "bambusa", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


@pytest.mark.parametrize(
    "fixture_name", ["function.bam", "global.bam"], ids=["function", "global"]
)
def test_cli_exit_code_is_zero(fixture_name: str) -> None:
    path = DATA_DIR / fixture_name
    result = _run_cli("parse", str(path))
    assert result.returncode == 0, result.stderr


def test_parse_tree_output_matches_golden() -> None:
    path = DATA_DIR / "function.bam"
    result = _run_cli("parse", str(path))
    assert result.returncode == 0, result.stderr
    expected = (DATA_DIR / "function_tree.txt").read_text().strip()
    assert result.stdout.strip() == expected


def test_parse_json_output_matches_golden() -> None:
    path = DATA_DIR / "global.bam"
    result = _run_cli("parse", str(path), "--format", "json")
    assert result.returncode == 0, result.stderr
    expected = (DATA_DIR / "global_tree.json").read_text().strip()
    assert result.stdout.strip() == expected


_SKIP_UNREADABLE = os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0)


@pytest.mark.skipif(
    _SKIP_UNREADABLE,
    reason="Restricted-permission test not supported on this platform",
)
def test_cli_handles_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "unreadable.bam"
    path.write_text("fn main() {}\n", encoding="utf-8")

    original_mode = stat.S_IMODE(path.stat().st_mode)
    path.chmod(0)
    try:
        result = _run_cli("parse", str(path))
    finally:
        path.chmod(original_mode)

    assert result.returncode == 1
    assert result.stderr.strip().splitlines()[-1] == f"bambusa: cannot read {path}"

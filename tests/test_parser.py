"""Tests for the Bambusa parser CLI."""

from __future__ import annotations

import os
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

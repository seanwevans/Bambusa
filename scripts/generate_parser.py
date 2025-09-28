#!/usr/bin/env python3
"""Generate the Bambusa ANTLR parser into ``src/bambusa/parser``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "Bambusa.g4"
OUTPUT_DIR = ROOT / "src" / "bambusa" / "parser"


def main() -> int:
    if not GRAMMAR.exists():
        print(f"Grammar not found: {GRAMMAR}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    cmd = [
        "antlr4",
        "-Dlanguage=Python3",
        str(GRAMMAR),
        "-o",
        str(OUTPUT_DIR),
    ]

    try:
        subprocess.run(cmd, check=True, cwd=ROOT, env=env)
    except FileNotFoundError:
        print("The 'antlr4' command is not available on PATH.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

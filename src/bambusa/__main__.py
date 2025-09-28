

"""Entry point for the ``bambusa`` console script."""

from __future__ import annotations

import argparse
import sys

from .parser import cli as parser_cli
from bambusa.cli.main import main

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bambusa", description="Bambusa language utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="Parse a Bambusa source file")
    parser_cli.configure_parse_subcommand(parse_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "parse":
        return parser_cli.handle_parse_command(args)

    parser.error(f"Unknown command: {args.command}")
    return 2




if __name__ == "__main__":
    raise SystemExit(main())

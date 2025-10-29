"""Command line helpers for the Bambusa parser."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import ParseTree

from .BambusaLexer import BambusaLexer
from .BambusaParser import BambusaParser


@dataclass
class BambusaSyntaxError(Exception):
    """Represents a syntax error encountered while parsing."""

    message: str
    line: int | None = None
    column: int | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        location = ""
        if self.line is not None and self.column is not None:
            location = f" (line {self.line}, column {self.column})"
        return f"{self.message}{location}"


class _CollectingErrorListener(ErrorListener):
    """Gather syntax errors from the lexer or parser."""

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[BambusaSyntaxError] = []

    def syntaxError(
        self,
        recognizer,  # type: ignore[override]
        offendingSymbol,
        line: int,
        column: int,
        msg: str,
        e,
    ) -> None:
        self.errors.append(BambusaSyntaxError(msg, line=line, column=column))

    def raise_if_errors(self) -> None:
        if self.errors:
            raise self.errors[0]


def configure_parse_subcommand(parser) -> None:
    """Configure the ``bambusa parse`` sub-command."""

    parser.add_argument("path", type=Path, help="Path to a Bambusa source file")
    parser.add_argument(
        "--format",
        choices=("tree", "json"),
        default="tree",
        help="Output format for the parse result",
    )


def _parse_source(path: Path) -> tuple[ParseTree, BambusaParser]:
    if not path.exists():
        raise FileNotFoundError(path)

    try:
        input_stream = FileStream(str(path), encoding="utf-8")
    except OSError as exc:
        raise OSError(str(path)) from exc

    lexer = BambusaLexer(input_stream)
    parser_error_listener = _CollectingErrorListener()
    lexer_error_listener = _CollectingErrorListener()

    lexer.removeErrorListeners()
    lexer.addErrorListener(lexer_error_listener)

    token_stream = CommonTokenStream(lexer)
    parser = BambusaParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(parser_error_listener)

    tree = parser.program()

    lexer_error_listener.raise_if_errors()
    parser_error_listener.raise_if_errors()

    return tree, parser


def _tree_to_mapping(node: ParseTree, parser: BambusaParser) -> dict[str, Any]:
    """Convert a parse tree into a JSON-serialisable mapping."""

    def _walk(current: ParseTree) -> dict[str, Any]:
        from antlr4 import TerminalNode

        if isinstance(current, TerminalNode):
            symbol = current.getSymbol()
            token_type = symbol.type
            if token_type == -1:
                token_name = "EOF"
            else:
                token_name = parser.symbolicNames[token_type]
            return {"type": token_name, "text": symbol.text}

        rule_name = parser.ruleNames[current.getRuleIndex()]
        children: Iterable[ParseTree] = list(current.getChildren() or [])
        return {
            "rule": rule_name,
            "children": [_walk(child) for child in children],
        }

    return _walk(node)


def handle_parse_command(args) -> int:
    """Execute the ``bambusa parse`` command."""

    try:
        tree, parser = _parse_source(args.path)
    except FileNotFoundError:
        print(f"bambusa: file not found: {args.path}", file=sys.stderr)
        return 1
    except OSError:
        print(f"bambusa: cannot read {args.path}", file=sys.stderr)
        return 1
    except BambusaSyntaxError as exc:
        print(f"bambusa: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        mapping = _tree_to_mapping(tree, parser)
        print(json.dumps(mapping, indent=2, sort_keys=True))
    else:
        print(tree.toStringTree(recog=parser))

    return 0


__all__ = [
    "BambusaSyntaxError",
    "configure_parse_subcommand",
    "handle_parse_command",
]

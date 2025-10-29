"""Command line interface for Bambusa utilities."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from bambusa.debug.timeline import Timeline
from bambusa.parser import cli as parser_cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bambusa", description="Bambusa developer tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse a Bambusa source file",
        description="Inspect the parse tree produced from Bambusa source code",
    )
    parser_cli.configure_parse_subcommand(parse_parser)

    timeline_parser = subparsers.add_parser(
        "timeline",
        help="Inspect a runtime execution log",
        description="Interactively explore a structured execution log produced by the runtime",
    )
    timeline_parser.add_argument("log", help="Path to the execution log produced by the runtime")
    timeline_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the entire timeline as JSON and exit",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "timeline":
        return run_timeline(args)
    if args.command == "parse":
        return parser_cli.handle_parse_command(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2


def run_timeline(args: argparse.Namespace) -> int:
    if args.log == "-":
        timeline = Timeline.from_stream(sys.stdin)
    else:
        timeline = Timeline.from_log(args.log)
    root = timeline.fork()

    if args.json:
        print(json.dumps(timeline.to_json(), indent=2, sort_keys=True))
        return 0

    stack: List[Timeline] = []
    current = timeline
    label_stack: List[str] = []
    current_label = "root"

    print(_format_banner(args.log, current))
    while True:
        try:
            raw = input(f"{current_label}@step{current.current_step}> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break
        if not raw:
            continue
        command, *rest = raw.split()

        try:
            if command in {"quit", "exit"}:
                break
            elif command == "help":
                _print_help()
            elif command in {"next", "n"}:
                current.next()
                _print_state(current)
            elif command in {"prev", "p"}:
                current.prev()
                _print_state(current)
            elif command == "goto":
                if not rest:
                    print("usage: goto <step>")
                    continue
                step = int(rest[0])
                current.seek(step)
                _print_state(current)
            elif command == "state":
                _print_state(current)
            elif command == "instruction":
                print(json.dumps(current.current_instruction, indent=2, sort_keys=True))
            elif command == "steps":
                print(f"steps: 0..{current.size - 1}")
            elif command == "fork":
                step = current.current_step
                if rest:
                    step = int(rest[0])
                stack.append(current)
                label_stack.append(current_label)
                current = current.fork(at_step=step)
                current_label = f"fork{len(stack)}"
                print(f"Forked timeline at step {current.current_step}")
                _print_state(current)
            elif command == "back":
                if not stack:
                    print("No parent timeline to return to")
                    continue
                current = stack.pop()
                current_label = label_stack.pop()
                print(f"Returned to timeline at step {current.current_step}")
            elif command == "diff":
                step = None
                if rest:
                    step = int(rest[0])
                diff = current.diff(root, step=step, other_step=step)
                print(json.dumps(diff, indent=2, sort_keys=True))
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
        except Exception as exc:  # pragma: no cover - interactive error path
            print(f"error: {exc}")
    return 0


def _format_banner(path: str, timeline: Timeline) -> str:
    return (
        f"Loaded timeline from {path}\n"
        "Commands: next, prev, goto <step>, state, instruction, steps, diff [step],\n"
        "          fork [step], back, help, quit"
    )


def _print_state(timeline: Timeline) -> None:
    payload = {
        "step": timeline.current_step,
        "instruction": timeline.current_instruction,
        "state": timeline.current_state,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def _print_help() -> None:
    print(
        "Available commands:\n"
        "  next / n        - advance to the next step\n"
        "  prev / p        - move to the previous step\n"
        "  goto <step>     - jump to a specific step\n"
        "  state           - show the current instruction and state\n"
        "  instruction     - show only the current instruction\n"
        "  steps           - show the valid step range\n"
        "  fork [step]     - fork a new timeline from the current (or specified) step\n"
        "  back            - return to the parent timeline\n"
        "  diff [step]     - diff against the root timeline at the current (or specified) step\n"
        "  help            - print this message\n"
        "  quit / exit     - leave the debugger"
    )


__all__ = ["main", "build_parser"]

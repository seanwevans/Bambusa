

"""Entry point for the ``bambusa`` console script."""

from __future__ import annotations

from bambusa.cli.main import main as cli_main


def main(argv: list[str] | None = None) -> int:
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

"""The command line.

Four exit codes, and the distinction between the last two is the point of this
program: 0 the claims hold, 1 you asked for something impossible, 2 a claim is
no longer true, 3 nothing could be checked.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn

from portfolio import __version__
from portfolio.errors import (
    EXIT_COULD_NOT_RUN,
    EXIT_OK,
    EXIT_USAGE,
    PortfolioError,
)
from portfolio.model import load
from portfolio.render import render, write
from portfolio.verify import Check, check_live, check_offline, enforce

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from collections.abc import Callable, Sequence

ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA: Final[Path] = ROOT / "projects.toml"
README: Final[Path] = ROOT / "README.md"


class _Parser(argparse.ArgumentParser):
    """An ArgumentParser that exits 1 on a usage error rather than 2.

    argparse's default collides with "a gate failed". Without this override, a
    misspelt flag and a claim that has stopped being true are the same number to
    a pipeline -- and a pipeline that cannot tell those apart will be taught to
    ignore both.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Build the parser with prefix matching turned off.

        `allow_abbrev` defaults to True, so argparse accepts any unambiguous
        prefix of a long option. This project's own test for "a misspelt flag
        is a usage error" passed `--liv` and got a full live verification
        against eight repositories, exit 0. A typo that silently does something
        is the exact failure this repository is about.
        """
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print(f"{self.prog}: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def _paths() -> _Parser:
    """The two path options, shared by every subcommand.

    Declared on a parent parser rather than only on the top-level one so that
    both ``portfolio --data X render`` and ``portfolio render --data X`` work.
    argparse binds a top-level option before the subcommand name and nowhere
    else, which reads as a bug to anyone who has used any other CLI.
    """
    common = _Parser(add_help=False)
    common.add_argument(
        "--data",
        type=Path,
        default=DATA,
        help="Path to projects.toml (default: the one in this repository).",
    )
    common.add_argument(
        "--readme",
        type=Path,
        default=README,
        help="Path to the generated README (default: the one in this repository).",
    )
    return common


def build_parser() -> _Parser:
    """Every command this tool has."""
    common = _paths()
    parser = _Parser(prog="portfolio", description=__doc__, parents=[common])
    parser.add_argument("--version", action="version", version=f"portfolio {__version__}")
    # parser_class so every subcommand inherits both the exit-1 behaviour and
    # allow_abbrev=False. `add_subparsers` otherwise builds plain
    # ArgumentParsers, and the overrides would apply only to the top level.
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    sub.add_parser("list", help="Print the projects, in reading order.", parents=[common])

    render_parser = sub.add_parser(
        "render", help="Generate README.md from projects.toml.", parents=[common]
    )
    render_parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit 2 if the file on disk differs from the data.",
    )

    verify_parser = sub.add_parser(
        "verify", help="Check that the published claims hold.", parents=[common]
    )
    verify_parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Also check each repository against GitHub and its documentation site. "
            "Needs `gh` and network. Not on the required path for a pull request."
        ),
    )

    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    portfolio = load(args.data)
    print(f"{portfolio.name} ({portfolio.owner}) - {len(portfolio)} projects\n")
    for project in portfolio.projects:
        print(f"{project.order}. {project.title}")
        print(f"   {project.tagline}")
        print(f"   {project.tests} tests, {project.coverage} coverage at {project.release}")
        print(f"   {project.repository_url}")
        print()
    return EXIT_OK


def _cmd_render(args: argparse.Namespace) -> int:
    portfolio = load(args.data)
    rendered = render(portfolio)
    if args.check:
        current = args.readme.read_text(encoding="utf-8") if args.readme.exists() else ""
        checks = check_offline(portfolio, current, rendered, args.data.parent)
        for check in checks:
            print(check)
        enforce(checks)
        print("\nthe index matches its data")
        return EXIT_OK
    path = write(portfolio, args.readme)
    print(f"wrote {path} from {args.data} ({len(portfolio)} projects)")
    return EXIT_OK


def _cmd_verify(args: argparse.Namespace) -> int:
    portfolio = load(args.data)
    rendered = render(portfolio)
    current = args.readme.read_text(encoding="utf-8") if args.readme.exists() else ""

    print("offline: the index matches its own data")
    checks: list[Check] = check_offline(portfolio, current, rendered, args.data.parent)
    for check in checks:
        print(check)

    if args.live:
        print("\nlive: the claims still hold in the world")
        for project in portfolio.projects:
            for check in check_live(project):
                print(check)
                checks.append(check)
    else:
        print("\n(skipping the live checks; pass --live to run them)")

    enforce(checks)
    print(f"\nall {len(checks)} claims hold")
    return EXIT_OK


COMMANDS: Final[dict[str, Callable[[argparse.Namespace], int]]] = {
    "list": _cmd_list,
    "render": _cmd_render,
    "verify": _cmd_verify,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and dispatch, turning a known error into its exit code."""
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except PortfolioError as error:
        print(f"{args.command}: {error}", file=sys.stderr)
        if error.remedy:
            print(error.remedy, file=sys.stderr)
        return error.exit_code
    except OSError as error:
        # A file that vanished, a directory that is not writable. Not a gate
        # failure: nothing was checked.
        print(f"{args.command}: {error}", file=sys.stderr)
        return EXIT_COULD_NOT_RUN


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

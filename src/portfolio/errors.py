"""Errors, each carrying the exit code a pipeline should see.

The same four codes the rest of this portfolio uses, for the same reason: a
pipeline that cannot tell "you typed the path wrong" from "a claim on the front
page is no longer true" will eventually be taught to ignore both.
"""

from __future__ import annotations

from typing import Final

#: The claims hold.
EXIT_OK: Final[int] = 0
#: A usage error. `argparse` would exit 2 here by default, which collides with
#: "a gate failed", so the parser is subclassed to return this instead.
EXIT_USAGE: Final[int] = 1
#: A gate failed: the README has drifted, or a live claim is no longer true.
EXIT_GATE_FAILED: Final[int] = 2
#: Could not run. Nothing was checked, which is not the same as nothing being
#: wrong -- a rate-limited API must never look like a passing verification.
EXIT_COULD_NOT_RUN: Final[int] = 3


class PortfolioError(Exception):
    """Base class. Carries a remedy, because an error without one is a puzzle."""

    exit_code: int = EXIT_COULD_NOT_RUN

    def __init__(self, message: str, *, remedy: str | None = None) -> None:
        """Record *message* and the *remedy* a reader should act on."""
        super().__init__(message)
        self.remedy = remedy


class ConfigError(PortfolioError):
    """The data file or the arguments are wrong."""

    exit_code = EXIT_USAGE


class GateError(PortfolioError):
    """A claim this repository publishes is no longer true."""

    exit_code = EXIT_GATE_FAILED


class UnreachableError(PortfolioError):
    """The live world could not be reached, so nothing was verified.

    Deliberately **not** a gate failure. A rate limit or a network blip is not
    evidence that a claim is false, and reporting it as one is how a check
    becomes noise that people learn to re-run until it passes.
    """

    exit_code = EXIT_COULD_NOT_RUN

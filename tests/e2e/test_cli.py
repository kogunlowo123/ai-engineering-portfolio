"""The CLI as a real process.

Exit codes and console encoding are invisible in process, and both have bitten
this series: argparse exits 2, which collides with "a gate failed", and Windows
prints through cp1252 by default.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from portfolio.errors import EXIT_OK, EXIT_USAGE

pytestmark = pytest.mark.e2e

ROOT = Path(__file__).resolve().parent.parent.parent


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "portfolio", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


class TestExitCodes:
    def test_a_usage_error_exits_one_not_two(self):
        # Two is "a claim is no longer true". Without the _Parser override a
        # misspelt flag and a decayed index are the same number to a pipeline.
        assert run("verify", "--liv").returncode == EXIT_USAGE

    def test_an_unknown_subcommand_exits_one(self):
        assert run("teleport").returncode == EXIT_USAGE

    def test_no_subcommand_exits_one(self):
        assert run().returncode == EXIT_USAGE

    def test_version_and_help_exit_zero(self):
        assert run("--version").returncode == EXIT_OK
        assert run("--help").returncode == EXIT_OK


class TestCommandsRun:
    def test_list_runs(self):
        result = run("list")
        assert result.returncode == EXIT_OK
        assert "projects" in result.stdout

    def test_verify_offline_passes(self):
        result = run("verify")
        assert result.returncode == EXIT_OK, result.stderr
        assert "claims hold" in result.stdout

    def test_render_check_passes(self):
        assert run("render", "--check").returncode == EXIT_OK

    def test_output_is_encodable_on_a_windows_console(self):
        # cp1252 cannot represent an em dash, and the failure lands at the
        # print rather than anywhere near the code that produced the string.
        for args in (("list",), ("verify",)):
            run(*args).stdout.encode("cp1252", errors="strict")

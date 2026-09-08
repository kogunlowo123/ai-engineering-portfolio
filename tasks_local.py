"""The task table. Run through ``python tasks.py <name>``.

Standard library only, because a task runner that needs its own dependency
installed before it can install dependencies is a bootstrap problem nobody
asked for.
"""

from __future__ import annotations

from collections.abc import Sequence


def _run(*args: str) -> list[str]:
    return ["uv", "run", *args]


def _portfolio(*args: str) -> list[str]:
    return _run("python", "-m", "portfolio", *args)


TASKS: dict[str, tuple[str, list[Sequence[str]]]] = {
    "setup": (
        "Install the project and its development tooling.",
        [["uv", "sync", "--locked", "--group", "dev"]],
    ),
    "fmt": ("Format.", [_run("ruff", "format", ".")]),
    "lint": (
        "Lint and check formatting.",
        [_run("ruff", "check", "."), _run("ruff", "format", "--check", ".")],
    ),
    "typecheck": ("Type check under mypy --strict.", [_run("mypy")]),
    "test": (
        "Run the test suite with the coverage gate. Live checks are deselected.",
        [_run("pytest", "--cov", "--cov-report=term-missing", "--cov-fail-under=98")],
    ),
    "test-unit": ("Unit tests only.", [_run("pytest", "-m", "unit")]),
    "test-integration": ("Integration tests only.", [_run("pytest", "-m", "integration")]),
    "test-e2e": ("The CLI as a real process.", [_run("pytest", "-m", "e2e")]),
    "test-meta": (
        "The verifier's own negative controls: break a claim, assert it goes red.",
        [_run("pytest", "-m", "meta")],
    ),
    "test-live": (
        "The live claims. Needs the network and an authenticated `gh`.",
        [_run("pytest", "-m", "live", "--no-cov")],
    ),
    # -- the generated index ------------------------------------------------
    "render": (
        "Regenerate README.md from projects.toml.",
        [_portfolio("render")],
    ),
    "render-check": (
        "Fail if README.md has drifted from projects.toml. The CI check.",
        [_portfolio("render", "--check")],
    ),
    "list": ("Print the projects, in reading order.", [_portfolio("list")]),
    "verify": (
        "Check the index against its own data. No network.",
        [_portfolio("verify")],
    ),
    "verify-live": (
        "Check every project is public, released, green, and its docs answer 200.",
        [_portfolio("verify", "--live")],
    ),
    "security": (
        "Local security scans.",
        [
            _run("bandit", "-c", "pyproject.toml", "-r", "src", "-f", "screen"),
            [
                "uv",
                "export",
                "--locked",
                "--no-emit-project",
                "--no-hashes",
                "--output-file",
                "requirements.audit.txt",
            ],
            [
                "uv",
                "tool",
                "run",
                "pip-audit",
                "--strict",
                "--no-deps",
                "--requirement",
                "requirements.audit.txt",
            ],
        ],
    ),
    "build": ("Build the wheel and sdist.", [["uv", "build"]]),
}

#: The order CI runs things in, cheapest gate first. `render-check` is early on
#: purpose: a drifted README is the failure this repository exists to catch, and
#: it costs a second to find.
ALL = ("lint", "typecheck", "render-check", "test", "verify")

# Expanded here rather than special-cased in the runner: tasks.py runs whatever
# command list it finds, and a task carrying an empty one would print nothing
# and exit 0. Nothing about that looks wrong on a terminal, which is what makes
# it worth catching.
TASKS["all"] = (
    "Everything CI runs, in the order CI runs it.",
    [step for name in ALL for step in TASKS[name][1]],
)

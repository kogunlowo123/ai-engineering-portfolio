"""Render ``README.md`` from ``projects.toml``.

The README is generated so that it cannot drift from the data the verifier
checks. `portfolio render --check` compares the file on disk against what the
data would produce and fails if they differ, which is what CI runs: a hand-edit
to the README is a change nobody's checker knows about, and this repository
exists to argue that unchecked claims decay.

Deliberately no template engine. The output is one document with a fixed shape,
and a dependency whose whole job is substituting strings into that shape would
be a larger surface than the sixty lines below.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from pathlib import Path

    from portfolio.model import Portfolio, Project

#: Written into the generated file so nobody edits it by hand and loses the
#: change on the next render.
BANNER = (
    "<!-- Generated from projects.toml by `portfolio render`. Do not edit by hand:\n"
    "     CI regenerates this file and fails if it differs. Edit projects.toml. -->"
)


def _project_section(index: int, project: Project) -> list[str]:
    """One project, as the block a reader scans."""
    stack = ", ".join(f"`{item}`" for item in project.stack)
    return [
        f"### {index}. [{project.title}]({project.repository_url})",
        "",
        f"*{project.tagline}*",
        "",
        project.finding,
        "",
        "<details><summary>What it does</summary>",
        "",
        *[f"* {capability}" for capability in project.capabilities],
        "",
        "</details>",
        "",
        f"**Stack:** {stack}  ",
        (
            f"**{project.tests} tests, {project.coverage} coverage** at "
            f"[{project.release}]({project.release_url})  "
        ),
        f"**Docs:** <{project.docs_url}>",
        "",
    ]


def render(portfolio: Portfolio) -> str:
    """Build the README."""
    lines: list[str] = [
        BANNER,
        "",
        "# AI engineering portfolio",
        "",
        f"Eight production-grade repositories by [{portfolio.name}]"
        f"(https://github.com/{portfolio.owner}). Each one ships a working system,"
        " and each one **measures whether the thing it is built to do actually"
        " works** — against a null chosen so the answer could come back no.",
        "",
        "Several of them came back no. Those are the interesting ones, and they"
        " are on the front page of their own repositories rather than in a"
        " footnote:",
        "",
        "* an ensemble of three detection layers measured **worse than one of its own inputs**;",
        "* a published data-contamination rule **could not order** contaminated"
        " and clean corpora on real data;",
        "* a circuit breaker **made things worse** in every case but the one it"
        " was designed for, and the one it helps with needs capacity nobody had"
        " budgeted;",
        "* a naive Bayes model matched a neural one at **p = 0.79**, with a fifth"
        " of the parameters.",
        "",
        "---",
        "",
        "## The projects",
        "",
        "In reading order, which is not build order — see [docs/order.md](docs/order.md).",
        "",
    ]

    for index, project in enumerate(portfolio.projects, start=1):
        lines.extend(_project_section(index, project))

    lines.extend(
        [
            "---",
            "",
            "## What is the same in all eight",
            "",
            "These are not eight variations on a tutorial. They share a set of"
            " positions, arrived at by being wrong first:",
            "",
            "* **A gate that has only ever been observed passing is"
            " indistinguishable from `exit 0`.** Every repository has a layer"
            " whose only job is to break something and assert the build goes"
            " red — a mutation gate, a leave-one-out fold, a corrupted corpus, a"
            " deliberately regressed baseline.",
            "* **Measure against a null that could win.** A spend-matched random"
            ' router, a null corpus, a simpler model. Without one, "it works" is'
            " a claim about having a bigger budget.",
            "* **Refuse rather than degrade.** A component that cannot do what it"
            " was asked says so. Silently falling back to something cheaper looks"
            " healthy, costs less, and is wrong — and the only symptom is a"
            " number nobody is watching.",
            "* **Publish the inconvenient number in the same paragraph as the"
            " headline.** Every one of these repositories states what its"
            " measurement cannot tell you, next to what it can.",
            "* **Determinism is structural, not aspirational.** Integer"
            " arithmetic on decision paths, content-addressed artefacts, seeded"
            " generators, and a replay check that refuses to publish a result it"
            " cannot reproduce.",
            "",
            "Python 3.12 throughout, `ruff` and `mypy --strict` clean, multi-layer"
            " test suites with real coverage gates, containers that are"
            " smoke-tested rather than merely built, and documentation published"
            " from the repository Markdown so a page cannot drift from its"
            " source.",
            "",
            "---",
            "",
            "## This repository",
            "",
            "The index is generated. `projects.toml` is the source of truth,"
            " `portfolio render` writes this file, and `portfolio verify` checks"
            " the claims:",
            "",
            "```bash",
            "portfolio verify           # the README matches the data (offline)",
            "portfolio verify --live    # every repo is public, released, green,"
            " and its docs answer 200",
            "```",
            "",
            "An index is a page full of claims that decay: a repository goes"
            " private, a release is deleted, a documentation site starts 404ing,"
            " a pipeline goes red. Nothing re-reads a hand-written list, so this"
            " one re-reads itself — weekly, and on demand. The offline check runs"
            " on every push; the live one is not on the required path, because a"
            " gate that fails on someone else's rate limit is a gate people learn"
            " to ignore.",
            "",
            "## License",
            "",
            "MIT. Each project is separately licensed in its own repository.",
            "",
        ]
    )
    return "\n".join(lines)


def write(portfolio: Portfolio, path: Path) -> Path:
    """Write the rendered README to *path*."""
    path.write_text(render(portfolio), encoding="utf-8")
    return path

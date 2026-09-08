"""Check that the claims in this index are still true.

Two modes, deliberately separated, because they fail for different reasons and
belong on different schedules.

**Offline** (`portfolio verify`) checks that ``README.md`` is exactly what
``projects.toml`` renders to. It needs no network, is deterministic, and runs on
every push. A drifted README is a claim nobody's checker knows about.

**Live** (`portfolio verify --live`) checks each project against reality: the
repository is public, the release tag exists, the latest run on ``main``
concluded successfully, and the documentation site answers 200. It runs weekly
and on demand, and **not** on the required path for a pull request.

That last decision is the interesting one. A network check on every pull request
fails on rate limits, on GitHub incidents, on a runner with no egress -- none of
which mean a claim is false. A gate that goes red for reasons nobody can act on
is a gate people learn to re-run until it passes, which is worse than not having
it. So an unreachable API exits **3, "could not run"**, never 2, "a gate
failed": *nothing was checked* and *nothing is wrong* must not be the same
signal.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - see `_gh`; a literal argv and no shell
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from portfolio.errors import ConfigError, GateError, UnreachableError

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from portfolio.model import Portfolio, Project

#: How long to wait for one HTTP request. Short: this checks liveness, not
#: throughput, and a slow answer is still an answer.
TIMEOUT_S: Final[float] = 20.0

#: What a healthy documentation site returns.
OK_STATUS: Final[int] = 200


@dataclass(frozen=True, slots=True)
class Check:
    """One claim, and whether it still holds."""

    project: str
    claim: str
    ok: bool
    detail: str

    def __str__(self) -> str:
        """One aligned line, so a wall of these can be read at a glance."""
        mark = "ok  " if self.ok else "FAIL"
        return f"  {mark}  {self.project:<28}{self.claim}" + (
            f"  ({self.detail})" if self.detail else ""
        )


def _gh(*args: str) -> str:
    """Run `gh` and return stdout, or explain that nothing could be checked."""
    try:
        result = subprocess.run(  # noqa: S603  # nosec B603 B607 - literal argv, no shell
            # `gh` is resolved from PATH deliberately: this is a developer
            # tool, and pinning an absolute path would break every install
            # that puts it somewhere else.
            ["gh", *args],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_S,
        )
    except FileNotFoundError as error:
        raise UnreachableError(
            "the GitHub CLI is not installed",
            remedy="Install `gh` and run `gh auth login`, or omit --live.",
        ) from error
    except subprocess.TimeoutExpired as error:
        raise UnreachableError(f"gh timed out after {TIMEOUT_S}s") from error
    if result.returncode != 0:
        raise UnreachableError(
            f"gh {' '.join(args)} failed: {result.stderr.strip()[:200]}",
            remedy=(
                "Check `gh auth status`. This exits 3 rather than 2 on purpose: "
                "nothing was verified, which is not the same as a claim being false."
            ),
        )
    return result.stdout


def _status(url: str) -> int:
    """The status code *url* returns, or a refusal that nothing was checked.

    Raises:
        ConfigError: if *url* is not https. The address is built from the owner
            handle and slug in ``projects.toml``, so it is data rather than a
            literal, and ``urlopen`` will happily open ``file://`` -- which
            would turn a data file into a local-file read. Checking the scheme
            is cheaper than reasoning about who can edit that file.
    """
    if not url.startswith("https://"):
        raise ConfigError(
            f"refusing to check a non-https URL: {url!r}",
            remedy="Documentation URLs are derived from the owner handle and slug.",
        )
    request = urllib.request.Request(url, method="GET")  # noqa: S310 - scheme checked above
    try:
        with urllib.request.urlopen(  # noqa: S310  # nosec B310 - https enforced above
            request, timeout=TIMEOUT_S
        ) as response:
            return int(response.status)
    except urllib.error.HTTPError as error:
        # An HTTP error *is* an answer: a 404 from a documentation site is
        # exactly the decay this command exists to catch.
        return int(error.code)
    except (urllib.error.URLError, TimeoutError) as error:
        raise UnreachableError(
            f"could not reach {url}: {error}",
            remedy="A network failure is not evidence that the site is down.",
        ) from error


def check_offline(portfolio: Portfolio, readme: str, rendered: str) -> list[Check]:
    """The README matches the data. No network."""
    return [
        Check(
            project="(index)",
            claim="README.md matches projects.toml",
            ok=readme == rendered,
            detail="" if readme == rendered else "run `portfolio render`",
        ),
        *[
            Check(
                project=project.slug,
                claim="appears in the rendered index",
                ok=project.repository_url in rendered,
                detail="",
            )
            for project in portfolio.projects
        ],
    ]


def check_live(project: Project) -> list[Check]:
    """Check one project against the live world."""
    view = json.loads(
        _gh(
            "repo",
            "view",
            f"{project.owner}/{project.slug}",
            "--json",
            "visibility,isArchived",
        )
    )
    visibility = str(view.get("visibility", "")).upper()
    archived = bool(view.get("isArchived", False))

    releases = json.loads(
        _gh(
            "release",
            "list",
            "--repo",
            f"{project.owner}/{project.slug}",
            "--json",
            "tagName",
            "--limit",
            "50",
        )
    )
    tags = {str(entry.get("tagName", "")) for entry in releases}

    runs = json.loads(
        _gh(
            "run",
            "list",
            "--repo",
            f"{project.owner}/{project.slug}",
            "--branch",
            "main",
            "--limit",
            "1",
            "--json",
            "conclusion",
        )
    )
    conclusion = str(runs[0].get("conclusion", "")) if runs else ""

    docs_status = _status(project.docs_url)

    return [
        Check(project.slug, "the repository is public", visibility == "PUBLIC", visibility),
        Check(project.slug, "the repository is not archived", not archived, ""),
        Check(
            project.slug,
            f"release {project.release} exists",
            project.release in tags,
            "" if project.release in tags else f"found {sorted(tags)}",
        ),
        Check(
            project.slug,
            "the latest run on main succeeded",
            conclusion == "success",
            conclusion or "no runs",
        ),
        Check(
            project.slug,
            "the documentation site answers 200",
            docs_status == OK_STATUS,
            str(docs_status),
        ),
    ]


def enforce(checks: list[Check]) -> None:
    """Raise if any check failed, listing every one rather than only the first."""
    failed = [check for check in checks if not check.ok]
    if failed:
        raise GateError(
            "claims this index publishes are no longer true:\n"
            + "\n".join(f"  - {check.project}: {check.claim} ({check.detail})" for check in failed),
            remedy=(
                "Fix the world or fix projects.toml, then re-render. An index "
                "that has stopped being true is worse than no index, because "
                "somebody is acting on it."
            ),
        )

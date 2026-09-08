"""The portfolio as data, and the rules about what a record may claim.

``projects.toml`` is the single source of truth. ``README.md`` is generated from
it, and every decaying claim in it is checked against the live world by
:mod:`portfolio.verify`.

**Why an index repository has a source tree at all.** A list of links is not
software, and wrapping one in a Dockerfile to satisfy a checklist would be
exactly the cargo cult the rest of this portfolio argues against. What is real
here is narrower and worth building: an index makes **claims that decay**. A
repository goes private, a release is deleted, a documentation site starts
404ing, a pipeline goes red -- and the index goes on saying otherwise, because
nothing re-reads it. So the code here is a *verifier*, and the README is
generated rather than written so that the two cannot drift.

Measured figures are dated to their release tag on purpose. "465 tests at
v0.1.0" stays true forever; "465 tests" becomes false the first time a
dependency bump lands somewhere. The verifier therefore never has to chase a
number that was never going to hold still.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from portfolio.errors import ConfigError

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from pathlib import Path

#: Every field a project record must carry. Listed rather than inferred from the
#: dataclass so that adding a field without deciding whether it is required is a
#: test failure rather than a record that validates with a hole in it.
REQUIRED: Final[tuple[str, ...]] = (
    "slug",
    "title",
    "order",
    "tagline",
    "release",
    "tests",
    "coverage",
    "stack",
    "capabilities",
    "finding",
)

#: A release tag must at least look like one. Not a semver parser: the point is
#: to catch an empty string or a stray "TBD", which is how a placeholder reaches
#: a published page.
TAG_PREFIX: Final[str] = "v"


@dataclass(frozen=True, slots=True)
class Project:
    """One repository in the portfolio.

    Attributes:
        owner: The GitHub account. Carried on the record rather than looked up
            from a module global, so a ``Project`` is self-describing and every
            URL below is a pure function of the record.
        slug: The repository name. Also the documentation-site path.
        title: Human-readable name for headings.
        order: Position in the published list. Editorial, not chronological --
            ``docs/order.md`` says why the build order is not the reading order.
        tagline: One line: what it is, in the terms someone scanning would use.
        release: The tag every measured figure below was taken at.
        tests: Test count **at release**. A string rather than an int because
            one project honestly reports two numbers for two platforms, and
            flattening that to one would make it wrong on one of them.
        coverage: Coverage at release.
        stack: What it is built on.
        capabilities: What it actually does.
        finding: The thing this repository is worth reading for. Usually a
            measurement that came back inconvenient.
    """

    owner: str
    slug: str
    title: str
    order: int
    tagline: str
    release: str
    tests: str
    coverage: str
    stack: tuple[str, ...]
    capabilities: tuple[str, ...]
    finding: str

    @property
    def repository_url(self) -> str:
        """Where the code is."""
        return f"https://github.com/{self.owner}/{self.slug}"

    @property
    def docs_url(self) -> str:
        """Where the published documentation is."""
        return f"https://{self.owner}.github.io/{self.slug}/"

    @property
    def release_url(self) -> str:
        """Where the release is."""
        return f"{self.repository_url}/releases/tag/{self.release}"


@dataclass(frozen=True, slots=True)
class Portfolio:
    """Every project, plus who owns them."""

    owner: str
    name: str
    projects: tuple[Project, ...]

    def __len__(self) -> int:
        """How many projects the portfolio holds."""
        return len(self.projects)

    def by_slug(self, slug: str) -> Project:
        """One project, or a refusal that lists the ones that exist."""
        for project in self.projects:
            if project.slug == slug:
                return project
        raise ConfigError(
            f"no project named {slug!r}",
            remedy=f"Known projects: {', '.join(p.slug for p in self.projects)}.",
        )


def _require(record: dict[str, Any], index: int) -> None:
    """Refuse a record missing a field, naming both the field and the record."""
    missing = [field for field in REQUIRED if field not in record]
    if missing:
        name = record.get("slug", f"the record at position {index + 1}")
        raise ConfigError(
            f"{name} is missing {missing}",
            remedy="Every project record carries every field; none are optional.",
        )


def load(path: Path) -> Portfolio:
    """Read and validate ``projects.toml``.

    Raises:
        ConfigError: on a missing file, a missing field, a duplicate slug, an
            order that is not a contiguous 1..N, or a release tag that does not
            look like a tag.
    """
    if not path.exists():
        raise ConfigError(
            f"no portfolio data at {path}",
            remedy="This file is the source of truth; README.md is generated from it.",
        )
    document = tomllib.loads(path.read_text(encoding="utf-8"))

    owner_table = document.get("owner", {})
    handle = str(owner_table.get("handle", ""))
    if not handle:
        raise ConfigError(
            "the [owner] table needs a handle",
            remedy="Every repository and documentation URL is derived from it.",
        )

    records = document.get("project", [])
    if not records:
        raise ConfigError("no projects; an index of nothing is not an index")

    projects: list[Project] = []
    for index, record in enumerate(records):
        _require(record, index)
        if not str(record["release"]).startswith(TAG_PREFIX):
            raise ConfigError(
                f"{record['slug']}: release {record['release']!r} does not look like a tag",
                remedy="A placeholder here becomes a broken link on a published page.",
            )
        projects.append(
            Project(
                owner=handle,
                slug=str(record["slug"]),
                title=str(record["title"]),
                order=int(record["order"]),
                tagline=str(record["tagline"]).strip(),
                release=str(record["release"]),
                tests=str(record["tests"]),
                coverage=str(record["coverage"]),
                stack=tuple(str(item) for item in record["stack"]),
                capabilities=tuple(str(item) for item in record["capabilities"]),
                finding=str(record["finding"]).strip(),
            )
        )

    slugs = [project.slug for project in projects]
    duplicates = {slug for slug in slugs if slugs.count(slug) > 1}
    if duplicates:
        raise ConfigError(f"duplicate slugs: {sorted(duplicates)}")

    orders = sorted(project.order for project in projects)
    if orders != list(range(1, len(projects) + 1)):
        raise ConfigError(
            f"order must be 1..{len(projects)} with no gaps or repeats, got {orders}",
            remedy="The order is the reading order of the published index.",
        )

    return Portfolio(
        owner=handle,
        name=str(owner_table.get("name", handle)),
        projects=tuple(sorted(projects, key=lambda project: project.order)),
    )

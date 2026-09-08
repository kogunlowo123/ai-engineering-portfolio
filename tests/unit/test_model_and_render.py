"""The data model and the renderer, in isolation."""

from __future__ import annotations

import pytest

from portfolio.cli import DATA
from portfolio.errors import ConfigError
from portfolio.model import Project, load
from portfolio.render import BANNER, render

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def real():
    """This repository's own data. The thing that actually ships."""
    return load(DATA)


class TestTheShippedData:
    def test_it_loads(self, real):
        assert len(real) == 8

    def test_every_project_is_in_reading_order(self, real):
        assert [p.order for p in real.projects] == list(range(1, len(real) + 1))

    def test_every_slug_is_unique(self, real):
        assert len({p.slug for p in real.projects}) == len(real)

    def test_every_project_has_a_finding_worth_reading(self, real):
        # The finding is why anyone would open the repository. A one-line
        # placeholder here would make the whole index a list of links.
        for project in real.projects:
            assert len(project.finding) > 80, project.slug

    def test_every_project_names_a_stack_and_capabilities(self, real):
        for project in real.projects:
            assert project.stack, project.slug
            assert len(project.capabilities) >= 3, project.slug

    def test_urls_are_derived_rather_than_written(self, real):
        for project in real.projects:
            assert project.repository_url == f"https://github.com/{real.owner}/{project.slug}"
            assert project.docs_url == f"https://{real.owner}.github.io/{project.slug}/"
            assert project.release_url.endswith(f"/releases/tag/{project.release}")

    def test_measured_figures_are_dated_to_a_release(self, real):
        # "465 tests" goes stale on the next dependency bump; "465 tests at
        # v0.1.0" stays true. The renderer must always print the two together.
        rendered = render(real)
        for project in real.projects:
            assert f"{project.tests} tests, {project.coverage} coverage" in rendered
            assert project.release in rendered

    def test_by_slug_finds_a_project(self, real):
        assert real.by_slug("domain-slm").title

    def test_by_slug_lists_the_alternatives_when_it_cannot(self, real):
        with pytest.raises(ConfigError) as caught:
            real.by_slug("nope")
        assert "Known projects" in (caught.value.remedy or "")


class TestRendering:
    def test_the_output_is_deterministic(self, real):
        assert render(real) == render(real)

    def test_it_carries_a_do_not_edit_banner(self, real):
        assert render(real).startswith(BANNER)

    def test_every_project_appears_with_its_links(self, real):
        rendered = render(real)
        for project in real.projects:
            assert project.repository_url in rendered
            assert project.docs_url in rendered
            assert project.release_url in rendered

    def test_projects_appear_in_reading_order(self, real):
        rendered = render(real)
        positions = [rendered.index(project.title) for project in real.projects]
        assert positions == sorted(positions)

    def test_it_states_what_the_portfolio_is_for(self, real):
        rendered = render(real)
        assert "measures whether" in rendered
        assert "came back no" in rendered


class TestValidation:
    def test_a_missing_file_says_what_it_is_for(self, tmp_path):
        with pytest.raises(ConfigError) as caught:
            load(tmp_path / "absent.toml")
        assert "source of truth" in (caught.value.remedy or "")

    def test_an_empty_owner_is_refused(self, tmp_path):
        path = tmp_path / "p.toml"
        path.write_text("[owner]\nname = 'x'\n", encoding="utf-8")
        with pytest.raises(ConfigError, match="needs a handle"):
            load(path)

    def test_a_file_with_no_projects_is_refused(self, tmp_path):
        path = tmp_path / "p.toml"
        path.write_text("[owner]\nhandle = 'x'\n", encoding="utf-8")
        with pytest.raises(ConfigError, match="index of nothing"):
            load(path)

    def test_a_project_is_frozen(self):
        project = Project(
            owner="o",
            slug="s",
            title="t",
            order=1,
            tagline="tag",
            release="v1",
            tests="1",
            coverage="1%",
            stack=("Python",),
            capabilities=("c",),
            finding="f",
        )
        with pytest.raises(AttributeError):
            project.slug = "other"  # type: ignore[misc]

"""The verifier's own negative controls: break one claim, assert it goes red.

This is the layer that makes the rest of this repository mean anything. A
verifier that has only ever been observed passing is indistinguishable from
``exit 0``, and an index whose checker cannot fail is a hand-written list with
extra steps.

Every test here has a green control before it, so a red result cannot be a fact
about a broken fixture.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from portfolio.errors import EXIT_GATE_FAILED, GateError
from portfolio.model import Portfolio, Project, load
from portfolio.render import render
from portfolio.verify import Check, check_offline, enforce

pytestmark = pytest.mark.meta


@pytest.fixture
def portfolio(tmp_path: Path) -> Portfolio:
    """A small, valid portfolio written to disk and read back."""
    path = tmp_path / "projects.toml"
    path.write_text(
        """
[owner]
handle = "someone"
name = "Someone"

[[project]]
slug = "alpha"
title = "Alpha"
order = 1
tagline = "The first one."
release = "v1.0.0"
tests = "10"
coverage = "99%"
stack = ["Python"]
capabilities = ["Does a thing"]
finding = "A finding."

[[project]]
slug = "beta"
title = "Beta"
order = 2
tagline = "The second one."
release = "v2.0.0"
tests = "20"
coverage = "98%"
stack = ["Python"]
capabilities = ["Does another thing"]
finding = "Another finding."
""",
        encoding="utf-8",
    )
    return load(path)


class TestTheGatePasses:
    def test_a_freshly_rendered_readme_matches_its_data(self, portfolio):
        # The control. Without it, every red result below could be a fact about
        # the checker rather than about the change.
        rendered = render(portfolio)
        checks = check_offline(portfolio, rendered, rendered)
        assert all(check.ok for check in checks)
        # Does not raise. `enforce` returns None, so the assertion is the
        # absence of a GateError rather than a value.
        enforce(checks)

    def test_the_shipped_index_matches_the_shipped_data(self):
        # The real one, not a fixture: this repository's own README must be
        # exactly what its own data renders to.
        from portfolio.cli import DATA, README

        real = load(DATA)
        checks = check_offline(real, README.read_text(encoding="utf-8"), render(real))
        assert all(check.ok for check in checks), [c for c in checks if not c.ok]

    def test_every_link_on_the_shipped_index_resolves(self):
        # The front page links into docs/. Nothing verified those files existed
        # until this check, which made them exactly the kind of claim this
        # repository is against: true when written, silently a 404 afterwards.
        from portfolio.cli import DATA, README

        real = load(DATA)
        rendered = render(real)
        checks = check_offline(real, README.read_text(encoding="utf-8"), rendered, DATA.parent)
        links = [check for check in checks if "the link to" in check.claim]
        assert links, "the index should link to at least one file in the repository"
        assert all(check.ok for check in links), [c for c in links if not c.ok]


class TestTheGateFires:
    def test_a_hand_edited_readme_fails(self, portfolio):
        # The failure this repository exists to prevent: somebody edits the
        # generated file, and the claim is now one no checker knows about.
        edited = render(portfolio).replace("Alpha", "Alpha (updated!)")
        with pytest.raises(GateError, match="no longer true"):
            enforce(check_offline(portfolio, edited, render(portfolio)))

    def test_a_missing_readme_fails(self, portfolio):
        with pytest.raises(GateError):
            enforce(check_offline(portfolio, "", render(portfolio)))

    def test_a_project_missing_from_the_index_fails(self, portfolio):
        # A record in the data that never reached the page. The offline check
        # asserts every project's URL appears, so dropping one from the
        # renderer cannot go unnoticed.
        rendered = render(portfolio)
        truncated = rendered.replace("https://github.com/someone/beta", "")
        checks = check_offline(portfolio, truncated, truncated)
        assert any(not check.ok and check.project == "beta" for check in checks)
        with pytest.raises(GateError):
            enforce(checks)

    def test_a_link_to_a_file_that_is_not_there_fails(self, tmp_path, portfolio):
        # The control: a link whose target exists passes. The banner links into
        # docs/ itself, so those files have to be present for the control to be
        # about the one link this test adds.
        (tmp_path / "docs").mkdir()
        for name in ("order.md", "verification.md", "there.md"):
            (tmp_path / "docs" / name).write_text("present", encoding="utf-8")
        present = render(portfolio) + "\nSee [docs/there.md](docs/there.md).\n"
        enforce(check_offline(portfolio, present, present, tmp_path))

        # The same page pointing one file to the left. A rename or a typo in a
        # relative link publishes a 404 and changes nothing a reader can see
        # from the source, so the checker has to be the one that notices.
        absent = render(portfolio) + "\nSee [docs/gone.md](docs/gone.md).\n"
        checks = check_offline(portfolio, absent, absent, tmp_path)
        assert any(not check.ok and "docs/gone.md" in check.claim for check in checks), checks
        with pytest.raises(GateError, match=re.escape("docs/gone.md")):
            enforce(checks)

    def test_absolute_and_fragment_links_are_not_treated_as_files(self, portfolio):
        # Every project URL on the page is an https link, and headings link by
        # fragment. Treating either as a path would fail every run and the
        # check would be turned off within a week.
        page = render(portfolio) + "\n[up](#top) [out](https://example.invalid/x)\n"
        checks = check_offline(portfolio, page, page, Path("/nonexistent-root"))
        claims = [check.claim for check in checks if "the link to" in check.claim]
        assert not [claim for claim in claims if "#top" in claim or "example" in claim]
        # Every project URL on the page is https too, and none became a path.
        assert not [claim for claim in claims if "github.com" in claim]

    def test_enforce_lists_every_failure_not_only_the_first(self, portfolio):
        checks = [
            Check("alpha", "a claim", ok=False, detail="one"),
            Check("beta", "another claim", ok=False, detail="two"),
        ]
        with pytest.raises(GateError) as caught:
            enforce(checks)
        message = str(caught.value)
        assert "alpha" in message
        assert "beta" in message

    def test_a_gate_failure_carries_exit_code_two(self, portfolio):
        with pytest.raises(GateError) as caught:
            enforce([Check("alpha", "a claim", ok=False, detail="")])
        assert caught.value.exit_code == EXIT_GATE_FAILED


class TestTheLiveCheckWouldFire:
    """The live checks, exercised without a network.

    `check_live` shells out to `gh`, so it is not run here. What *is* run is the
    thing that decides pass from fail, because a verifier that builds correct
    `Check` records and then evaluates them wrongly would pass every offline
    test in this file.
    """

    @pytest.mark.parametrize(
        ("claim", "detail"),
        [
            ("the repository is public", "PRIVATE"),
            ("release v1.0.0 exists", "found []"),
            ("the latest run on main succeeded", "failure"),
            ("the documentation site answers 200", "404"),
        ],
    )
    def test_each_live_failure_mode_raises(self, claim, detail):
        with pytest.raises(GateError, match="no longer true"):
            enforce([Check("alpha", claim, ok=False, detail=detail)])

    def test_a_passing_live_check_does_not_raise(self):
        enforce([Check("alpha", "the repository is public", ok=True, detail="PUBLIC")])


class TestTheDataIsValidated:
    def test_a_record_missing_a_field_is_refused(self, tmp_path):
        from portfolio.errors import ConfigError

        path = tmp_path / "projects.toml"
        path.write_text(
            '[owner]\nhandle = "x"\n\n[[project]]\nslug = "a"\ntitle = "A"\n',
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="is missing"):
            load(path)

    def test_a_placeholder_release_is_refused(self, portfolio, tmp_path):
        # "TBD" in a release field becomes a broken link on a published page.
        from portfolio.errors import ConfigError

        path = tmp_path / "bad.toml"
        path.write_text(
            '[owner]\nhandle = "x"\n\n[[project]]\nslug = "a"\ntitle = "A"\norder = 1\n'
            'tagline = "t"\nrelease = "TBD"\ntests = "1"\ncoverage = "1%"\n'
            'stack = ["Python"]\ncapabilities = ["c"]\nfinding = "f"\n',
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="does not look like a tag"):
            load(path)

    def test_a_duplicate_slug_is_refused(self, tmp_path):
        from portfolio.errors import ConfigError

        body = (
            '[[project]]\nslug = "a"\ntitle = "A"\norder = {order}\n'
            'tagline = "t"\nrelease = "v1"\ntests = "1"\ncoverage = "1%"\n'
            'stack = ["Python"]\ncapabilities = ["c"]\nfinding = "f"\n'
        )
        path = tmp_path / "dup.toml"
        path.write_text(
            '[owner]\nhandle = "x"\n\n' + body.format(order=1) + body.format(order=2),
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="duplicate slugs"):
            load(path)

    def test_a_gap_in_the_order_is_refused(self, tmp_path):
        # The order is the reading order of the published index; a gap means
        # somebody deleted a project and did not renumber.
        from portfolio.errors import ConfigError

        path = tmp_path / "gap.toml"
        path.write_text(
            '[owner]\nhandle = "x"\n\n'
            '[[project]]\nslug = "a"\ntitle = "A"\norder = 1\ntagline = "t"\n'
            'release = "v1"\ntests = "1"\ncoverage = "1%"\nstack = ["P"]\n'
            'capabilities = ["c"]\nfinding = "f"\n\n'
            '[[project]]\nslug = "b"\ntitle = "B"\norder = 3\ntagline = "t"\n'
            'release = "v1"\ntests = "1"\ncoverage = "1%"\nstack = ["P"]\n'
            'capabilities = ["c"]\nfinding = "f"\n',
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="no gaps"):
            load(path)

    def test_every_required_field_is_a_field_of_the_dataclass(self):
        # A field added to Project without being added to REQUIRED would let a
        # record validate with a hole in it.
        from dataclasses import fields

        from portfolio.model import REQUIRED

        names = {field.name for field in fields(Project)}
        assert set(REQUIRED) <= names
        # `owner` comes from the [owner] table rather than from each record.
        assert names - set(REQUIRED) == {"owner"}

    def test_a_replaced_record_still_renders(self, portfolio):
        # Guards the renderer against assuming anything about field contents.
        odd = replace(portfolio.projects[0], title="A & B <C>", tagline="")
        assert odd.title in render(replace(portfolio, projects=(odd, portfolio.projects[1])))

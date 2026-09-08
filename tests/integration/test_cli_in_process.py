"""The CLI driven in process.

A subprocess is a different interpreter, so coverage cannot see it. An earlier
project in this series left its CLI at 0% coverage for exactly that reason and
found two real defects the first time it was driven in process. Both layers
exist here, deliberately.
"""

from __future__ import annotations

import pytest

from portfolio.cli import DATA, build_parser, main
from portfolio.errors import EXIT_GATE_FAILED, EXIT_OK, EXIT_USAGE

pytestmark = pytest.mark.integration


class TestParser:
    def test_every_registered_command_is_dispatchable(self):
        from portfolio.cli import COMMANDS

        actions = [a for a in build_parser()._actions if a.dest == "command"]
        assert actions
        assert set(actions[0].choices or ()) == set(COMMANDS)

    def test_no_subcommand_is_a_usage_error(self):
        with pytest.raises(SystemExit) as caught:
            build_parser().parse_args([])
        assert caught.value.code == EXIT_USAGE


class TestList:
    def test_it_prints_every_project(self, capsys):
        assert main(["list"]) == EXIT_OK
        printed = capsys.readouterr().out
        assert "domain-slm" in printed
        assert "8 projects" in printed


class TestRender:
    def test_check_passes_against_the_shipped_readme(self, capsys):
        assert main(["render", "--check"]) == EXIT_OK
        assert "matches its data" in capsys.readouterr().out

    def test_it_writes_a_readme_that_then_checks_clean(self, tmp_path, capsys):
        out = tmp_path / "README.md"
        assert main(["render", "--readme", str(out)]) == EXIT_OK
        assert out.exists()
        capsys.readouterr()
        assert main(["render", "--check", "--readme", str(out)]) == EXIT_OK

    def test_check_fails_on_a_hand_edited_readme(self, tmp_path, capsys):
        out = tmp_path / "README.md"
        main(["render", "--readme", str(out)])
        out.write_text(out.read_text(encoding="utf-8") + "\nedited\n", encoding="utf-8")
        capsys.readouterr()
        assert main(["render", "--check", "--readme", str(out)]) == EXIT_GATE_FAILED
        assert "portfolio render" in capsys.readouterr().err

    def test_check_fails_when_there_is_no_readme(self, tmp_path, capsys):
        assert (
            main(["render", "--check", "--readme", str(tmp_path / "none.md")]) == EXIT_GATE_FAILED
        )


class TestVerify:
    def test_offline_verification_passes_on_the_shipped_index(self, capsys):
        assert main(["verify"]) == EXIT_OK
        printed = capsys.readouterr().out
        assert "claims hold" in printed
        assert "skipping the live checks" in printed

    def test_a_bad_data_file_is_a_usage_error(self, tmp_path, capsys):
        bad = tmp_path / "bad.toml"
        bad.write_text("[owner]\nhandle = 'x'\n", encoding="utf-8")
        assert main(["verify", "--data", str(bad)]) == EXIT_USAGE

    def test_a_missing_data_file_is_a_usage_error(self, tmp_path):
        assert main(["list", "--data", str(tmp_path / "absent.toml")]) == EXIT_USAGE


class TestTheDataFileShips:
    def test_it_is_where_the_cli_expects(self):
        assert DATA.exists()


class TestTheLiveBranch:
    """`verify --live` in process, with the world replaced.

    The live path is the one that cannot be exercised on a pull request, which
    is exactly why it needs a test that does not need the network.
    """

    def test_live_verification_reports_and_passes(self, monkeypatch, capsys):
        from portfolio import cli
        from portfolio.verify import Check

        monkeypatch.setattr(
            cli,
            "check_live",
            lambda project: [Check(project.slug, "is fine", ok=True, detail="")],
        )
        assert main(["verify", "--live"]) == EXIT_OK
        printed = capsys.readouterr().out
        assert "the claims still hold in the world" in printed
        assert "all 17 claims hold" in printed

    def test_a_failed_live_claim_exits_two(self, monkeypatch, capsys):
        from portfolio import cli
        from portfolio.verify import Check

        monkeypatch.setattr(
            cli,
            "check_live",
            lambda project: [Check(project.slug, "is public", ok=False, detail="PRIVATE")],
        )
        assert main(["verify", "--live"]) == EXIT_GATE_FAILED
        assert "no longer true" in capsys.readouterr().err

    def test_an_unreachable_world_exits_three_not_two(self, monkeypatch, capsys):
        # The distinction the whole design turns on: nothing was checked, which
        # is not the same as a claim being false.
        from portfolio import cli
        from portfolio.errors import EXIT_COULD_NOT_RUN, UnreachableError

        def unreachable(project):
            raise UnreachableError("rate limited", remedy="try later")

        monkeypatch.setattr(cli, "check_live", unreachable)
        assert main(["verify", "--live"]) == EXIT_COULD_NOT_RUN
        assert "rate limited" in capsys.readouterr().err


class TestUnreadableFiles:
    def test_an_unreadable_readme_is_reported_rather_than_crashing(self, monkeypatch, capsys):
        from portfolio.errors import EXIT_COULD_NOT_RUN

        def boom(*_args, **_kwargs):
            raise OSError("disk went away")

        monkeypatch.setattr("pathlib.Path.read_text", boom)
        assert main(["verify"]) == EXIT_COULD_NOT_RUN
        assert "disk went away" in capsys.readouterr().err

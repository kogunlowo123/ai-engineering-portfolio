"""The live verifier's failure semantics, exercised without a network.

The distinction under test is the one this program exists for: **"nothing could
be checked" is not "a claim is false".** An unreachable API must exit 3, never
2, or the weekly check becomes noise that people re-run until it passes.

`gh` and `urllib` are replaced rather than called. That is not squeamishness
about the network: a test that needs GitHub to be down cannot be written any
other way, and the branch it covers is precisely the one that only runs when
something is wrong.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
from collections.abc import Callable
from email.message import Message
from typing import Any

import pytest

from portfolio.errors import EXIT_COULD_NOT_RUN, GateError, UnreachableError
from portfolio.model import Project
from portfolio.verify import check_live, enforce

pytestmark = pytest.mark.unit


def _project(**overrides: Any) -> Project:
    base = {
        "owner": "someone",
        "slug": "alpha",
        "title": "Alpha",
        "order": 1,
        "tagline": "t",
        "release": "v1.0.0",
        "tests": "10",
        "coverage": "99%",
        "stack": ("Python",),
        "capabilities": ("c",),
        "finding": "f",
    }
    return Project(**{**base, **overrides})


class _Result:
    """Just enough of CompletedProcess for the code under test."""

    def __init__(self, stdout: str = "", returncode: int = 0, stderr: str = "") -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def _gh_returning(payloads: list[str]) -> Callable[..., _Result]:
    """A fake `gh` that answers each call in order."""
    calls = iter(payloads)

    def fake(*_args: Any, **_kwargs: Any) -> _Result:
        return _Result(stdout=next(calls))

    return fake


HEALTHY = [
    json.dumps({"visibility": "PUBLIC", "isArchived": False}),
    json.dumps([{"tagName": "v1.0.0"}]),
    json.dumps([{"conclusion": "success"}]),
]


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class TestALiveCheckThatPasses:
    def test_a_healthy_project_produces_five_passing_checks(self, monkeypatch):
        monkeypatch.setattr(subprocess, "run", _gh_returning(HEALTHY))
        monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: _Response(200))
        checks = check_live(_project())
        assert len(checks) == 5
        assert all(check.ok for check in checks)
        enforce(checks)


class TestEachClaimCanFail:
    @pytest.mark.parametrize(
        ("payloads", "status", "failing"),
        [
            (
                [
                    json.dumps({"visibility": "PRIVATE", "isArchived": False}),
                    json.dumps([{"tagName": "v1.0.0"}]),
                    json.dumps([{"conclusion": "success"}]),
                ],
                200,
                "the repository is public",
            ),
            (
                [
                    json.dumps({"visibility": "PUBLIC", "isArchived": True}),
                    json.dumps([{"tagName": "v1.0.0"}]),
                    json.dumps([{"conclusion": "success"}]),
                ],
                200,
                "the repository is not archived",
            ),
            (
                [
                    json.dumps({"visibility": "PUBLIC", "isArchived": False}),
                    json.dumps([{"tagName": "v0.9.0"}]),
                    json.dumps([{"conclusion": "success"}]),
                ],
                200,
                "release v1.0.0 exists",
            ),
            (
                [
                    json.dumps({"visibility": "PUBLIC", "isArchived": False}),
                    json.dumps([{"tagName": "v1.0.0"}]),
                    json.dumps([{"conclusion": "failure"}]),
                ],
                200,
                "the latest run on main succeeded",
            ),
            (HEALTHY, 404, "the documentation site answers 200"),
        ],
    )
    def test_the_failing_claim_is_named(self, monkeypatch, payloads, status, failing):
        monkeypatch.setattr(subprocess, "run", _gh_returning(payloads))
        monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: _Response(status))
        checks = check_live(_project())
        failed = [check for check in checks if not check.ok]
        assert [check.claim for check in failed] == [failing]
        with pytest.raises(GateError):
            enforce(checks)

    def test_a_repository_with_no_runs_at_all_fails(self, monkeypatch):
        # An empty run list is not a success. Reading `.[0]` off it would raise,
        # and treating "no runs" as "fine" would let a repository whose CI was
        # deleted keep its green claim.
        monkeypatch.setattr(
            subprocess,
            "run",
            _gh_returning(
                [
                    json.dumps({"visibility": "PUBLIC", "isArchived": False}),
                    json.dumps([{"tagName": "v1.0.0"}]),
                    json.dumps([]),
                ]
            ),
        )
        monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: _Response(200))
        failed = [check for check in check_live(_project()) if not check.ok]
        assert failed[0].detail == "no runs"


class TestUnreachableIsNotAFailedClaim:
    """The distinction this module exists to protect."""

    def test_a_missing_gh_exits_three_not_two(self, monkeypatch):
        def missing(*_a: Any, **_k: Any) -> _Result:
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", missing)
        with pytest.raises(UnreachableError) as caught:
            check_live(_project())
        assert caught.value.exit_code == EXIT_COULD_NOT_RUN

    def test_a_failing_gh_exits_three_and_says_why(self, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *_a, **_k: _Result(returncode=1, stderr="rate limit exceeded"),
        )
        with pytest.raises(UnreachableError) as caught:
            check_live(_project())
        assert "rate limit" in str(caught.value)
        assert "not the same as a claim being false" in (caught.value.remedy or "")

    def test_a_gh_timeout_exits_three(self, monkeypatch):
        def slow(*_a: Any, **_k: Any) -> _Result:
            raise subprocess.TimeoutExpired(cmd="gh", timeout=1)

        monkeypatch.setattr(subprocess, "run", slow)
        with pytest.raises(UnreachableError) as caught:
            check_live(_project())
        assert caught.value.exit_code == EXIT_COULD_NOT_RUN

    def test_an_unreachable_docs_host_exits_three(self, monkeypatch):
        monkeypatch.setattr(subprocess, "run", _gh_returning(HEALTHY))

        def unreachable(*_a: Any, **_k: Any) -> None:
            raise urllib.error.URLError("no route to host")

        monkeypatch.setattr("urllib.request.urlopen", unreachable)
        with pytest.raises(UnreachableError) as caught:
            check_live(_project())
        assert caught.value.exit_code == EXIT_COULD_NOT_RUN

    def test_an_http_error_is_an_answer_not_an_outage(self, monkeypatch):
        # A 404 from a documentation site is exactly the decay this command
        # exists to catch, so it must become a *failed claim* rather than an
        # "unreachable". The two are one `except` clause apart.
        monkeypatch.setattr(subprocess, "run", _gh_returning(HEALTHY))

        def gone(*_a: Any, **_k: Any) -> None:
            raise urllib.error.HTTPError(
                url="https://example.invalid/",
                code=404,
                msg="Not Found",
                hdrs=Message(),
                fp=None,
            )

        monkeypatch.setattr("urllib.request.urlopen", gone)
        checks = check_live(_project())
        failed = [check for check in checks if not check.ok]
        assert failed[0].detail == "404"
        with pytest.raises(GateError):
            enforce(checks)

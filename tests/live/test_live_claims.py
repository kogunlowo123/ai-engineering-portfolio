"""The live claims, checked against the real world.

Marked `live` and deselected by default: these need the network and an
authenticated `gh`. They run on a schedule and on demand, never on the required
path for a pull request -- a gate that fails on somebody else's rate limit is a
gate people learn to re-run until it passes.
"""

from __future__ import annotations

import shutil

import pytest

from portfolio.cli import DATA
from portfolio.model import load
from portfolio.verify import check_live, enforce

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(shutil.which("gh") is None, reason="needs the GitHub CLI"),
]


@pytest.fixture(scope="module")
def portfolio():
    return load(DATA)


def test_every_published_claim_still_holds(portfolio):
    checks = [check for project in portfolio.projects for check in check_live(project)]
    failed = [c for c in checks if not c.ok]
    assert not failed, "\n".join(str(c) for c in failed)
    enforce(checks)

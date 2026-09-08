# How this index checks itself

An index is a page full of claims that decay. A repository goes private, a
release is deleted, a documentation site starts 404ing, a pipeline goes red —
and a hand-written list goes on saying otherwise, because nothing re-reads it.

So this one re-reads itself.

## Two checks, on two schedules, for two different reasons

### Offline: the page matches its data

```bash
portfolio verify          # or: portfolio render --check
```

`projects.toml` is the source of truth and `README.md` is generated from it.
This check regenerates the file and compares. It needs no network, is
deterministic, and runs **on every push**.

It catches two failures. The first is somebody editing the generated file:
that edit is a claim no checker knows about, which is the whole thing this
repository argues against.

The second is a **relative link that no longer resolves**. The front page links
into `docs/`, and this repository shipped those links for exactly one commit
with nothing verifying the files were there — rename or move one and the
published page 404s silently, with nothing in the source looking any different.
So every Markdown link on the rendered page that is not `https:`, `mailto:` or
a bare `#fragment` is resolved against the repository root, and a miss is a
failed claim like any other.

### Live: the claims still hold in the world

```bash
portfolio verify --live
```

For each of the eight projects:

| Claim | How it is checked |
| --- | --- |
| the repository is public | `gh repo view --json visibility` |
| the repository is not archived | `gh repo view --json isArchived` |
| the release named in the data exists | `gh release list --json tagName` |
| the latest run on `main` succeeded | `gh run list --json conclusion` |
| the documentation site answers 200 | one HTTP GET |

Forty claims across eight repositories, plus eleven offline ones.

## Why the live check is not on the required path

This is the design decision worth defending.

A network check on every pull request fails on rate limits, on GitHub
incidents, on a runner with no egress. **None of those mean a claim is false.**
A gate that goes red for reasons nobody can act on is a gate people learn to
re-run until it passes, and at that point it is worse than not having one — it
is a green tick that means nothing.

So the live check runs **weekly and on demand**, and its failure modes are kept
distinct:

| Exit | Meaning |
| --- | --- |
| 0 | The claims hold. |
| 1 | Usage error. |
| 2 | **A claim is no longer true.** Something in the world moved. |
| 3 | **Nothing could be checked.** `gh` missing, rate limited, host unreachable. |

An unreachable API exits **3, never 2**. *Nothing was checked* and *nothing is
wrong* must not be the same signal, and `tests/unit/test_verify_semantics.py`
holds that open by replacing `gh` and `urllib` with doubles that fail in each
way.

## Measured figures are dated, so they cannot rot

Every test count and coverage figure in the index is written **at a release
tag**:

> 465 tests, 90% coverage at v0.1.0

"465 tests" becomes false the first time a dependency bump lands anywhere. "465
tests at v0.1.0" stays true forever, and the verifier never has to chase a
number that was never going to hold still. The renderer prints the figure and
the tag together, and a test asserts it.

## The verifier's own negative controls

`tests/meta/` breaks one claim at a time and asserts the check goes red: a
hand-edited README, a missing README, a project dropped from the page, a record
with a missing field, a placeholder release tag, a duplicate slug, a gap in the
ordering. Each has a green control before it, so a red result cannot be a fact
about a broken fixture.

A verifier that has only ever been observed passing is a hand-written list with
extra steps.

## Adding or changing a project

1. Edit `projects.toml`. Nothing else is the source of truth.
2. `portfolio render` to regenerate the README.
3. Commit both. CI fails if they disagree.
4. `portfolio verify --live` to confirm the new claims are true before pushing.

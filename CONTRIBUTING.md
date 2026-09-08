# Contributing

This repository is an index. The rule that matters is short.

## The one rule

**`projects.toml` is the source of truth. `README.md` is generated.**

Editing the README by hand is the failure this repository exists to catch: the
edit becomes a claim no checker knows about, and CI will fail on the next push.

```bash
# after editing projects.toml
python tasks.py render          # regenerate README.md
python tasks.py verify-live     # confirm the new claims are actually true
git add projects.toml README.md
```

## Prerequisites

- Python 3.12 (the project pins `>=3.12,<3.13`)
- [uv](https://docs.astral.sh/uv/) 0.10 or newer
- The [GitHub CLI](https://cli.github.com/), authenticated — only for the live
  checks

## Development loop

| Task | Command |
| --- | --- |
| Format | `python tasks.py fmt` |
| Lint and format check | `python tasks.py lint` |
| Types | `python tasks.py typecheck` |
| Tests with the coverage gate | `python tasks.py test` |
| One layer | `python tasks.py test-unit` (also `-integration`, `-e2e`, `-meta`) |
| Regenerate the index | `python tasks.py render` |
| Fail if the index drifted | `python tasks.py render-check` |
| Offline verification | `python tasks.py verify` |
| Live verification | `python tasks.py verify-live` |
| Security scans | `python tasks.py security` |
| **Everything CI runs** | `python tasks.py all` |

## Adding a project

Add a `[[project]]` table to `projects.toml` with every field — none are
optional, and `load` refuses a record with a hole in it. Then:

* give it an `order`, and renumber the others so the orders are a contiguous
  `1..N`. A gap means somebody deleted a project and did not look at the list;
* write the `finding` as the thing the repository is worth reading for, not a
  summary of what it does. The capabilities list is for what it does. A finding
  under 80 characters fails a test, because a placeholder there turns the whole
  index into a list of links;
* date the measured figures to the release tag. "465 tests" goes stale on the
  next dependency bump; "465 tests at v0.1.0" stays true, and the renderer
  always prints the two together.

## The test layers

| Layer | What only it can see |
| --- | --- |
| `unit` | The data model, the renderer, and the verifier's failure semantics with `gh` and `urllib` replaced. |
| `integration` | The CLI in process, which is the only way coverage sees it. |
| `e2e` | The CLI as a real process: exit codes and console encoding. |
| `meta` | The verifier's own negative controls. Break a claim, assert it goes red. |
| `live` | The real world. Deselected by default; runs weekly. |

`meta` is the layer that matters. A verifier that has only ever been observed
passing is a hand-written list with extra steps.

## Style

* **Comments say why, not what.** A comment explaining why the obvious approach
  was rejected is the most valuable thing in a file.
* **Refuse rather than degrade.** Every error carries a `remedy` saying what to
  run.
* **Keep exit 2 and exit 3 apart.** "A claim is false" and "nothing could be
  checked" are different facts, and a check that conflates them becomes noise
  people re-run until it passes.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

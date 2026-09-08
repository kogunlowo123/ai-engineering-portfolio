# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] — 2026-09-08

### Fixed

* **Every relative link on the rendered page is now resolved against the
  repository.** The front page linked `docs/order.md` and nothing checked the
  file was there; a rename or a move would have published a 404 with nothing in
  the source looking any different. That is precisely the kind of claim this
  repository exists to argue against, and it was shipped on the repository
  itself. Links that are `https:`, `mailto:` or a bare `#fragment` are left
  alone — a check that failed on every project URL would be turned off inside a
  week. A `meta` test breaks one link and asserts the gate goes red, with a
  green control before it.
* **`docs/verification.md` is linked from the front page.** It is the full
  account of what is checked and why the live check is scheduled rather than
  required, and it was reachable only by browsing the tree.
* **The negative control for the B310 fix.** `_status` refuses a URL that is not
  `https:` before opening it, and no test exercised that branch — the single
  uncovered line in the repository was the security check itself.
* **The coverage figure was wrong.** 0.1.0 was published as 100% and measured
  99%; the entry above has been corrected to what it actually was. Coverage is
  now genuinely 100%, and `--cov-fail-under=100` in CI makes it a gate rather
  than a sentence in a document.

## [0.1.0] — 2026-09-08

First release. An index of eight AI engineering repositories that checks its own
claims.

### Added

* **`projects.toml` as the single source of truth**, with validation that
  refuses a record missing a field, a placeholder release tag, a duplicate slug,
  or an ordering that is not a contiguous `1..N`.
* **A generated `README.md`.** `portfolio render` writes it; `portfolio render
  --check` fails if the file on disk has drifted. A hand-edit to a generated
  page is a claim no checker knows about.
* **`portfolio verify --live`** — for each project: the repository is public and
  not archived, the release named in the data exists, the latest run on `main`
  succeeded, and the documentation site answers 200. Forty live claims across
  eight repositories, plus nine offline ones.
* **Four exit codes**, with the distinction between the last two as the point:
  0 the claims hold, 1 usage, 2 a claim is no longer true, 3 nothing could be
  checked. An unreachable API exits 3, never 2.
* **71 tests at 99% coverage** across five layers, including a `meta` layer
  whose only job is to break one claim at a time and assert the check goes red,
  and a `live` layer deselected by default.
* A weekly `live.yml` workflow, deliberately off the pull-request path.

### Notable decisions

* **Measured figures are dated to a release tag.** "465 tests" goes stale on the
  next dependency bump anywhere; "465 tests at v0.1.0" stays true, so the
  verifier never has to chase a number that was never going to hold still.
* **The live check is not required for a pull request.** A network check that
  fails on somebody else's rate limit is a gate people learn to re-run until it
  passes, and at that point it is worse than not having one.
* **No container, and that is deliberate.** This is a generator and a checker
  with no runtime dependencies and nothing to serve. Wrapping it in a Dockerfile
  to satisfy a checklist would be exactly the cargo cult the indexed projects
  argue against.

### Fixed during development

* **argparse accepted `--liv` as an abbreviation of `--live`.** The test for "a
  misspelt flag is a usage error" passed that abbreviation and got a full live
  verification against eight repositories, exit 0. `allow_abbrev=False` is now
  set on the parser and inherited by every subcommand through `parser_class`. A
  typo that silently does something is the exact failure this repository is
  about.
* **Global options only bound before the subcommand.** `portfolio render
  --readme X` was a usage error while `portfolio --readme X render` worked,
  which reads as a bug to anyone who has used another CLI. Both work now, via a
  shared parent parser.
* **A dead `differs()` helper** in the renderer, superseded by `check_offline`
  and never called. Removed rather than left for a reader to wonder about.

[Unreleased]: https://github.com/kogunlowo123/ai-engineering-portfolio/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/kogunlowo123/ai-engineering-portfolio/releases/tag/v0.1.1
[0.1.0]: https://github.com/kogunlowo123/ai-engineering-portfolio/releases/tag/v0.1.0

# Security scan annotations and exceptions

An allowlist entry without a justification is a suppressed finding, which is
indistinguishable from an unnoticed one. Everything suppressed here is listed
with the reason.

## Static-analysis annotations

`bandit` findings are fixed or annotated in place, never silenced by lowering
the severity floor. The complete list in this repository:

| Location | Finding | Why it is annotated rather than fixed |
| --- | --- | --- |
| `src/portfolio/verify.py` (import) | B404 — the `subprocess` module | This program's whole job under `--live` is asking `gh` what the world looks like. See the two rows below for how the call itself is constrained |
| `src/portfolio/verify.py` `_gh` | B603 — `subprocess` call | The argument vector is a literal list built in that function; no shell is involved and nothing a caller supplies reaches it. The only variable parts are subcommand names and a repository slug from `projects.toml` |
| `src/portfolio/verify.py` `_gh` | B607 — partial executable path | `gh` is resolved from `PATH` deliberately. This is a developer tool; pinning an absolute path would break every installation that puts `gh` somewhere else, and would not add security on a machine where `PATH` is already attacker-controlled |
| `src/portfolio/verify.py` `_status` | B310 — `urlopen` scheme | **Fixed rather than suppressed.** The URL is derived from data in `projects.toml`, and `urlopen` will happily open `file://`, so the function refuses anything that is not `https://` before opening it. The annotation records that the check exists |

## One finding that was fixed, not annotated

B310 is worth calling out because the first instinct was to annotate it. The
documentation URL is built from the owner handle and slug in `projects.toml`,
which makes it **data rather than a literal**, and `urllib.request.urlopen`
supports `file:` and `ftp:`. A crafted data file could therefore have turned a
liveness check into a local-file read.

The scheme check is three lines and removes the question entirely. Annotating it
would have recorded a judgement about who can edit `projects.toml`, which is a
judgement that stops being true the moment somebody accepts a pull request.

## Dependency exceptions

| Identifier | Package | Why not fixed | Review by |
| --- | --- | --- | --- |
| _(none)_ | | | |

This project has **no runtime dependencies**, so `pip-audit` has only the
development toolchain to consider. That is the intended steady state, and the
table above should stay empty.

## Process, if an exception is ever needed

1. Confirm the finding is real and reachable from this codebase.
2. Add a row with the identifier, the reason it cannot be fixed now, the
   compensating control, and a review date no more than 90 days out.
3. Add the identifier to `security/audit-ignores.txt`.
4. Remove both entries as soon as a fixed version exists.

An exception whose review date has passed is a build failure, not a rubber
stamp.

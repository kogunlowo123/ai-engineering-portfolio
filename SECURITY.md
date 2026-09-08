# Security policy

## Reporting

Report privately through GitHub's [Security
Advisories](https://github.com/kogunlowo123/ai-engineering-portfolio/security/advisories/new)
form rather than opening a public issue.

Expect an acknowledgement within 5 working days. This is a portfolio project
maintained by one person, so that is an honest target rather than a commercial
SLA.

**For a vulnerability in one of the eight indexed projects, report it in that
project's own repository.** This one only links to them.

## What this repository holds

**Nothing sensitive.** It contains a TOML file of public repository names, a
generated Markdown page, and a program that reads both. There are no
credentials, no personal data, and no proprietary material. `gitleaks` runs over
the working tree and the full history on every push, which makes it a guard
against future mistakes rather than a current need.

## What it does at runtime

Two things worth naming, because both touch the outside world, and both happen
only under `--live`:

* **it shells out to `gh`** with a literal argument vector — no shell is
  involved, and nothing a caller supplies reaches the command line;
* **it makes one HTTP GET per project**, to a URL derived from the owner handle
  and slug in `projects.toml`.

At rest it has no runtime dependencies at all: `tomllib` is in the standard
library, the renderer is string concatenation, and there is no server.

## In scope

* **Anything that makes `portfolio verify` report success while a claim is
  false.** That is the one thing this program is for, and a verifier that passes
  wrongly is worse than no verifier.
* Argument injection or shell execution through `projects.toml`.
* Path traversal through the `--data` or `--readme` options.
* **An `UnreachableError` path that should be a `GateError`, or the reverse.**
  The distinction between "nothing could be checked" and "a claim is false" is
  load-bearing, and collapsing it in either direction is a real defect: one
  direction turns a rate limit into a false alarm, the other turns a real
  regression into silence.

## Out of scope

* **The absence of a container.** This is a generator and a checker with nothing
  to serve. The reasoning is in the module docstring of
  `src/portfolio/model.py`.
* Findings in the eight indexed repositories — report those in their own
  repositories, each of which has its own security policy.
* A scanner's raw output with no analysis.

## What is scanned, and when

| Tool | Scope | When |
| --- | --- | --- |
| `gitleaks` | Working tree **and full history** | Every push, every PR, weekly |
| `bandit` | `src/` | Every push, every PR, weekly |
| `pip-audit` | The exported locked dependency set | Every push, every PR, weekly |
| CodeQL | Python | Every push, every PR, weekly |

## Supported versions

The `main` branch. There are no maintained release branches.

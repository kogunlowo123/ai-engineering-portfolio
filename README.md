<!-- Generated from projects.toml by `portfolio render`. Do not edit by hand:
     CI regenerates this file and fails if it differs. Edit projects.toml. -->

# AI engineering portfolio

Eight production-grade repositories by [Kayode Ogunlowo](https://github.com/kogunlowo123). Each one ships a working system, and each one **measures whether the thing it is built to do actually works** — against a null chosen so the answer could come back no.

Several of them came back no. Those are the interesting ones, and they are on the front page of their own repositories rather than in a footnote:

* an ensemble of three detection layers measured **worse than one of its own inputs**;
* a published data-contamination rule **could not order** contaminated and clean corpora on real data;
* a circuit breaker **made things worse** in every case but the one it was designed for, and the one it helps with needs capacity nobody had budgeted;
* a naive Bayes model matched a neural one at **p = 0.79**, with a fifth of the parameters.

---

## The projects

In reading order, which is not build order — see [docs/order.md](docs/order.md).

### 1. [RAG research assistant](https://github.com/kogunlowo123/rag-research-assistant)

*Retrieval with verified citations, measured grounding, and a refusal threshold.*

Grounding is measured per sentence and the service **refuses** below a
threshold. A RAG system that always answers is a RAG system whose citations
nobody has checked.

<details><summary>What it does</summary>

* Hybrid retrieval: dense vectors and BM25 over a persisted inverted index, fused with RRF, diversified with MMR
* Trust-level prompt construction with nonce fences around retrieved text
* Citation verification and per-sentence grounding, with a refusal threshold rather than a confident guess
* Layered prompt-injection defence on retrieved documents
* Per-tenant isolation enforced in SQL, not in application code
* Pluggable embedding providers (fastembed, Ollama, OpenAI-compatible, hashing) with an extractive fallback

</details>

**Stack:** `FastAPI`, `SQLAlchemy 2 (async)`, `NumPy`, `PostgreSQL`, `Docker`  
**465 tests, 90% coverage** at [v0.1.0](https://github.com/kogunlowo123/rag-research-assistant/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/rag-research-assistant/>

### 2. [Bounded support agent](https://github.com/kogunlowo123/ai-support-agent)

*An agent that escalates rather than asserting a fact no tool returned.*

The verifier is the product. Fifteen real defects surfaced while writing its
tests, including an unreachable `ESCALATED` transition that crashed the agent
**at the moment it decided to be careful**, and an advisory step budget that
appended past its own maximum.

<details><summary>What it does</summary>

* Explicit state machine with a checked transition table
* Step and wall-clock budgets enforced as hard ceilings, not advice
* Permissioned tool registry with circuit breakers and idempotency keys
* Deterministic intent classification and planning; policy computed in code
* A verifier that escalates rather than sending any sentence asserting a fact no tool returned
* 31-scenario gate including adversarial and identity categories

</details>

**Stack:** `FastAPI`, `Pydantic`, `Docker`  
**502 tests, 88% coverage** at [v0.1.0](https://github.com/kogunlowo123/ai-support-agent/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/ai-support-agent/>

### 3. [Sandboxed MCP server](https://github.com/kogunlowo123/mcp-developer-server)

*Read-only developer tools in a contained workspace, with results marked untrusted.*

Everything the server returns is labelled **untrusted**. A file in a repository
is attacker-controlled input the moment the repository has contributors, and an
MCP server that hands it to a model unmarked is an injection channel with a
protocol around it.

<details><summary>What it does</summary>

* Read-only source-code tools inside a contained workspace
* Path containment that survives symlinks, junctions and traversal
* Secret redaction on every result before it leaves the sandbox
* Tool output marked untrusted, so a model cannot mistake it for instruction
* Implements MCP revision 2026-07-28

</details>

**Stack:** `Model Context Protocol (revision 2026-07-28)`, `asyncio`, `Docker`  
**527 on Linux, 520 on Windows (7 symlink cases skipped) tests, 91% coverage** at [v0.1.0](https://github.com/kogunlowo123/mcp-developer-server/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/mcp-developer-server/>

### 4. [Evaluations that fail builds](https://github.com/kogunlowo123/ai-evals-regression-suite)

*An eval harness with a baseline, real exit codes, and a gate on the gate.*

The **meta-gate**: `aievals mutate` corrupts a response the suite *accepted* and
asserts the verdict flips. It found a real hole in this repository's own example
suite during development. A suite that has only ever been observed passing is
indistinguishable from `exit 0`.

<details><summary>What it does</summary>

* Committed baseline with per-case and aggregate rules selected by run mode
* Exit 2 for 'a gate failed' and 3 for 'the harness could not run'
* Eleven deterministic mutators, each declaring what it applies to
* Grading as a pure function of the response, so the meta-gate costs no extra model calls

</details>

**Stack:** `Python`, `Docker`  
**618 tests, 96% coverage** at [v0.1.0](https://github.com/kogunlowo123/ai-evals-regression-suite/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/ai-evals-regression-suite/>

### 5. [LLM observability you can gate on](https://github.com/kogunlowo123/llmops-observability)

*Cost against a versioned price book, and burn-rate budgets that exit non-zero.*

Dashboards are not a control. This ships a **command that fails a pipeline**
when an objective is missed, which is the difference between observability and
a wall of graphs nobody is paged by.

<details><summary>What it does</summary>

* Cost accounting against a versioned price book, so a price change is a diff
* Multi-window burn-rate error budgets
* A command that exits non-zero when an objective is missed
* Telemetry designed to be gated on rather than looked at

</details>

**Stack:** `OpenTelemetry`, `Prometheus`, `Docker`  
**461 tests, 94.76% coverage** at [v0.1.0](https://github.com/kogunlowo123/llmops-observability/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/llmops-observability/>

### 6. [A small domain model you can trust](https://github.com/kogunlowo123/domain-slm)

*A tokenizer and classifier from scratch, and an evaluation that refuses to guess.*

The published contamination rule (13-gram containment >= 0.5) was inherited,
measured, and **found not to transfer**: data disjoint by construction scored
1.80% while the genuine test split scored 1.25%, so a threshold on it decides on
noise. Calibrating against a null corpus fixes it. Also published: naive Bayes
matches the neural model at p = 0.79 with a fifth of the parameters.

<details><summary>What it does</summary>

* BPE tokenizer and classifier trained from scratch on CPU in seconds
* Contamination detection calibrated against a null corpus
* Refuses to report a metric when the split it was measured on overlaps training
* Digest gates for integer artefacts, tolerance gates for float ones

</details>

**Stack:** `NumPy`, `Docker`  
**345 tests, 95.79% coverage** at [v0.1.0](https://github.com/kogunlowo123/domain-slm/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/domain-slm/>

### 7. [A firewall that publishes its own bypass rate](https://github.com/kogunlowo123/prompt-injection-firewall)

*Hold out an attack technique and the countermeasures it motivated, then report what gets through.*

**The ensemble was worse than one of its own inputs.** A noisy-OR of three
layers measured 20.89% bypass; the model layer alone measured 2.08%. The weak
layers fire on benign traffic, which pushes the 1%-FPR threshold from 0.11 to
0.79. The repository ships the configuration the measurement selected, and
publishes the cost (realised FPR 1.25% to 1.84%) in the same paragraph.

<details><summary>What it does</summary>

* Leave-one-family-out evaluation: hold out a technique *and* the rules it motivated
* Three detection layers, with the ensemble measured rather than assumed
* Wilson intervals on every published rate
* False-positive budget enforced at a matched realised rate, not just a matched target

</details>

**Stack:** `Python`, `Docker`  
**262 tests, 91.87% coverage** at [v0.1.0](https://github.com/kogunlowo123/prompt-injection-firewall/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/prompt-injection-firewall/>

### 8. [A gateway that measures its own routing](https://github.com/kogunlowo123/ai-model-gateway)

*A fitted router against a spend-matched null, and a breaker that sometimes makes things worse.*

Three: the router's **quality** generalises (+0.46 optimism gap) while its
**budget** does not (1.87x to 5.10x on the same thresholds); a self-validating
cascade answers 99.96% and is correct 77.38%; and a circuit breaker serves 21%
of traffic on a small pool and 99.6% on a large one, because **failover needs
capacity**.

<details><summary>What it does</summary>

* Routes between model tiers by predicted difficulty, fitted by IRLS
* Every headline measured against a spend-matched null that could have won
* Discrete-event simulation on integer virtual time, so concurrency results replay exactly
* Retry, circuit breakers and an end-to-end deadline that covers queueing
* OpenAI-compatible HTTP surface with a provenance block on every completion

</details>

**Stack:** `FastAPI`, `Discrete-event simulation`, `Docker`, `Ollama (optional)`  
**241 tests, 92.95% coverage** at [v0.1.0](https://github.com/kogunlowo123/ai-model-gateway/releases/tag/v0.1.0)  
**Docs:** <https://kogunlowo123.github.io/ai-model-gateway/>

---

## What is the same in all eight

These are not eight variations on a tutorial. They share a set of positions, arrived at by being wrong first:

* **A gate that has only ever been observed passing is indistinguishable from `exit 0`.** Every repository has a layer whose only job is to break something and assert the build goes red — a mutation gate, a leave-one-out fold, a corrupted corpus, a deliberately regressed baseline.
* **Measure against a null that could win.** A spend-matched random router, a null corpus, a simpler model. Without one, "it works" is a claim about having a bigger budget.
* **Refuse rather than degrade.** A component that cannot do what it was asked says so. Silently falling back to something cheaper looks healthy, costs less, and is wrong — and the only symptom is a number nobody is watching.
* **Publish the inconvenient number in the same paragraph as the headline.** Every one of these repositories states what its measurement cannot tell you, next to what it can.
* **Determinism is structural, not aspirational.** Integer arithmetic on decision paths, content-addressed artefacts, seeded generators, and a replay check that refuses to publish a result it cannot reproduce.

Python 3.12 throughout, `ruff` and `mypy --strict` clean, multi-layer test suites with real coverage gates, containers that are smoke-tested rather than merely built, and documentation published from the repository Markdown so a page cannot drift from its source.

---

## This repository

The index is generated. `projects.toml` is the source of truth, `portfolio render` writes this file, and `portfolio verify` checks the claims:

```bash
portfolio verify           # the README matches the data (offline)
portfolio verify --live    # every repo is public, released, green, and its docs answer 200
```

An index is a page full of claims that decay: a repository goes private, a release is deleted, a documentation site starts 404ing, a pipeline goes red. Nothing re-reads a hand-written list, so this one re-reads itself — weekly, and on demand. The offline check runs on every push; the live one is not on the required path, because a gate that fails on someone else's rate limit is a gate people learn to ignore.

## License

MIT. Each project is separately licensed in its own repository.

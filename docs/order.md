# Why the reading order is not the build order

The index lists eight repositories in an order that is an **editorial
decision**, not the order they were written in. This page says what the decision
was and why, because an unexplained ordering reads as arbitrary and an
arbitrary ordering wastes the first thirty seconds of every person who opens it.

## The order

| Read | Built | Repository |
| --- | --- | --- |
| 1 | 1 | `rag-research-assistant` |
| 2 | 2 | `ai-support-agent` |
| 3 | 3 | `mcp-developer-server` |
| 4 | 4 | `ai-evals-regression-suite` |
| 5 | 5 | `llmops-observability` |
| 6 | 6 | `domain-slm` |
| 7 | 7 | `prompt-injection-firewall` |
| 8 | 8 | `ai-model-gateway` |

They coincide here, and that is worth being honest about rather than inventing a
rearrangement to look deliberate. The build order was chosen to move from the
systems most people recognise to the ones that make the sharper argument, so it
already reads the way it should.

What follows is the reasoning, which stays useful if a ninth project ever
changes the shape.

## The three groups

**Systems you would recognise (1-3).** Retrieval, an agent, a protocol server.
These answer "can this person build the thing everyone is building". They are
first because a reader who bounces off an unfamiliar argument in the first entry
never reaches the rest.

**Things that judge other things (4-5).** An evaluation harness and an
observability pipeline. The shift is from *building* a system to *deciding
whether it is working*, which is where most of the difficulty in this field
actually is.

**Measurements that came back inconvenient (6-8).** A small model with a
contamination check that refuses to report a number; a firewall that publishes
its own bypass rate; a gateway whose circuit breaker mostly makes things worse.
These are last because they are the ones worth arguing about, and because they
only land once a reader has seen that the earlier systems are real.

## If you only read one

**`prompt-injection-firewall`**, for the result: an ensemble of three detection
layers measured *worse than one of its own inputs*, and the repository ships the
configuration the measurement selected rather than the one that sounds better.

**`ai-evals-regression-suite`**, if you care about process: the meta-gate
corrupts a response the suite accepted and asserts the verdict flips, and it
found a real hole in that repository's own example suite.

**`ai-model-gateway`**, if you care about distributed systems: a circuit breaker
that serves 21% of traffic on a small pool and 99.6% on a large one, because
failover needs capacity nobody had budgeted.

## For a specific role

* **Applied AI / LLM engineering** — 1, 2, 8, then 4.
* **ML platform or evaluation** — 4, 5, 6, then 1.
* **Security engineering** — 7, 3, then 2.
* **Backend or distributed systems** — 8, 5, then 1. Repository 8 is the one
  with a discrete-event simulator, a bounded pool and an end-to-end deadline.

## What is the same in all of them

Listed in the [index](../README.md), and it is the real content: every one has a
layer whose only job is to make its own gate go red, every headline is measured
against a null that could have won, and every one publishes what its
measurement cannot tell you next to what it can.

# ADR 001 — Router-first, with one bounded tool loop

- **Status:** accepted
- **Date:** 2026-09-05
- **Deciders:** application engineer of record; reviewed by the pilot review board
- **Supersedes:** the `demo_v0.py` single-call prototype

## Context

Murshid's traffic, from the analysis behind `data/replay_200.jsonl`, is roughly
70% FAQ-shaped, 25% transactional and 5% escalation. Three patterns were on the
table: a single agentic loop for everything, a fixed workflow for everything, or a
router dispatching to specialised handlers.

The pressure to pick the agent is real and it is not technical. It is that the
word is in the market.

## Decision

**Router first.** A cheap classifier assigns one of three intents and dispatches:

- `faq` → a single call against the service directory, cacheable, cheap model;
- `service` → a fixed workflow whose middle is a **bounded** tool loop
  (6 iterations, allowed-tool list, authorisation gate on side effects);
- `escalate` → a human. Not a model call at all.

The tool loop is the course's only agentic component, and it is bounded on every
axis that can run away: iterations, tokens, tool list, and a trace of every call.

## Consequences

**Good.** Each path is testable in isolation (`tests/pipeline/test_stages.py`).
Cost follows traffic shape rather than worst case: after Module 6's routing table
the FAQ path costs about 1/20th of the flagship path, and 70% of traffic takes it.
A misroute is *measurable* — it is a stratum in the golden set — where an agent's
wrong turn is a transcript somebody has to read.

**Bad.** Two more moving parts than a single call, and a router that is wrong
sends a citizen down the wrong path. We accept this because the misroute rate is
measured and gated, and because the failure is legible: a wrong route produces a
wrong-shaped answer, not a quietly expensive loop.

**Rejected: agent-first.** The decomposition here is known at design time. An
agentic loop would buy flexibility we do not need and pay for it in unbounded
cost, undebuggable traces, and a review board conversation we could not win. The
rule stands: start at the simplest pattern the use case allows; escalate on
evidence, not on vocabulary.

**Rejected: workflow-only.** A fixed chain for FAQ traffic would run the tool
schemas and the workflow prompt for every "what is the fee?" — paying the
transactional price for conversational traffic.

## Evidence

`BENCHMARKS.md`, Module 6 table: cost per conversation 4.07 → 0.37 halalas across
the routing change, with the evaluation suite green at every step.

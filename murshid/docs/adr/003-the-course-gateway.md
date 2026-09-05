# ADR 003 — The course runs against a simulator, on purpose

- **Status:** accepted
- **Date:** 2026-09-05
- **Applies to:** every default in this repository

## Context

A five-day course cannot depend on twenty-four participants each holding a working
provider key, a network that reaches it, and a provider having a good afternoon
during the one hour a drill is scheduled. Nor can its test suite: a repository
whose tests need credentials has tests that do not run.

Two of the course's best moments are also *faults*: the 429 storm in Module 2 and
the provider outage in Module 1. Waiting for a real provider to misbehave on cue
is not a lesson plan.

## Decision

Ship a gateway (`infra/mockgw`) that speaks both wire dialects — OpenAI chat
completions and Anthropic Messages — and answers from rules. Every route in
`configs/murshid.yaml` points at it by default. Every lab, test and eval run works
on a laptop with no key, no network and no GPU.

What is **real** in it: the wire contract, token accounting, `finish_reason`
control flow, tool calls, structured outputs, streaming frames, the HTTP error
taxonomy, prompt-cache hits keyed on a genuinely byte-stable prefix, fault
injection on demand, and grounding — answers are composed from the service
directory that arrives in the prompt, so a fact that is not in the directory
cannot appear in an answer.

What is **simulated**: quality. The "model tiers" differ by rules — how often a
tier guesses a fee, fumbles a tool contract, or fails a schema — not by
capability. The degradations are a hash of the input, so a run repeats exactly and
a gate that fires, fires for a reason you can point at.

## Consequences

**Good.** The drills are reproducible: `make drill-429`, `make drill-outage`. CI
is hermetic and free. A participant who breaks their environment is five minutes
from working, not an hour. And the substitution to a real provider is two
environment variables, which makes Module 1's boundary argument something
participants *perform* rather than something they are told.

**Bad, and stated everywhere it matters.** Numbers measured here are numbers about
this simulator. They are correct as measurements of the harness, the guards, the
meter and the gates — the things this course actually teaches — and they are not
evidence about any model's quality. Every artefact that reports numbers
(`BENCHMARKS.md`, `EVALUATION_REPORT.md`, the gateway's own module docstring)
carries that caveat in its first paragraph, because a caveat in an appendix is a
caveat nobody read.

**The honest test of this decision:** point a route at a real provider and re-run
the same harness, unchanged. If that is not a two-variable change, this ADR was
wrong and the boundary leaked.

```bash
export MURSHID_PRIMARY_BASE_URL=https://api.openai.com/v1
export MURSHID_PRIMARY_API_KEY=sk-...
make eval        # same suite, same asserts, different evidence
```

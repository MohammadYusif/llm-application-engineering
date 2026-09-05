# ADR 002 — Model choice is a routing table, not a winner

- **Status:** accepted
- **Date:** 2026-09-05
- **Revisit:** quarterly, or on any provider deprecation notice

## Context

"Which model?" was asked as a single question with a single answer. It is not one.
Murshid has three kinds of traffic with different constraints:

| Traffic | Volume | Constraint that decides |
|---|---|---|
| FAQ, no personal data | ~70% | unit cost |
| Service transactions, tool calling | ~25% | tool-contract reliability |
| Anything a data classification pins on-premise | varies | residency, absolutely |

## Decision

Route, do not choose:

```yaml
routing_table:
  faq:      murshid-small       # with a cascade — see below
  service:  murshid-default
  complex:  murshid-flagship
  escalate: null                # humans are not a model call
```

Residency-classified traffic goes to the `vllm` route regardless of the table.
That is possible **only** because every model call goes through the `LLMClient`
boundary; without it, "route by data classification" would be a rewrite rather
than a config entry.

The FAQ route carries a **cascade**: the small model answers first, and the answer
escalates to the flagship when it states an amount the service directory does not
contain (`murshid.pipeline.groundedness.unsupported_amounts`). The escalation
signal is deterministic and cheap, and it is the same check the evaluation harness
gates on. Model self-report — "was that hard?" — was rejected: it is weak,
sycophantic, and would have made the cascade a coin flip with extra steps.

## Evidence

Measured on this repository's own golden set, not on a leaderboard:

| Backend | Overall | ar | safety | service | Cost per suite |
|---|---|---|---|---|---|
| flagship | 100% | 100% | 100% | 100% | 65.0 hal |
| small | 95% | 95% | 100% | 83% | 2.7 hal |
| open-weight (vLLM) | 94% | 92% | 100% | 75% | 26.0 hal |

The `service` slice is where the small and open-weight models actually lose —
tool contracts, not prose — which is exactly why the routing table sends service
traffic to the mid tier and FAQ traffic to the small one.

Routing without the cascade **failed the gate** (faq −6pt, ar −5pt). With it,
the suite is at baseline and the cost is unchanged, because on this traffic the
cascade escalated zero times.

## Self-hosting

`scripts/breakeven.py`, at SAR 12/GPU-hour, 950 tok/s measured, 1.35× ops
overhead: self-hosting crosses over against the **flagship** tier at roughly 25%
sustained utilisation and **never** beats the cheap hosted tier.

Recommendation: keep the GPU for residency-bound and flagship-tier traffic. Do not
migrate FAQ traffic onto it to raise utilisation — that is paying more to look
busier.

## Snapshot policy

Model ids are pinned in `configs/murshid.yaml` and never referenced as literals in
code. A provider deprecation notice is a change ticket: run the harness against
the replacement, compare slices, update the config, update this ADR. The
re-litigation becomes a re-run.

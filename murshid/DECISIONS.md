# Decisions

The architecture decision records live in [`docs/adr/`](docs/adr/). This page is
the index, plus the one section a review board always asks for and most projects
cannot answer: what did you change your mind about?

| ADR | Decision | Status |
|---|---|---|
| [001](docs/adr/001-architecture-pattern.md) | Router-first, with exactly one bounded tool loop | accepted |
| [002](docs/adr/002-model-and-routing.md) | Model choice is a routing table, not a winner | accepted |
| [003](docs/adr/003-the-course-gateway.md) | The course runs against a simulator, on purpose | accepted |

## Trade-offs we reversed

### The routing table, reversed once and then re-shaped

**First decision.** Send FAQ traffic — 70% of turns — to the small model. The
arithmetic was overwhelming: 91% off the cost per conversation.

**What happened.** The evaluation gate blocked it. Not on the average, which
looked fine, but on two slices: `intent=faq` fell 6 points and `language=ar` fell
5. The failing cases were all out-of-directory questions, where the small model
stopped saying "I don't know" and started producing a plausible fee.

**What we did not do.** Move the intent up a tier and hand back the saving. That
is the reflex, and it treats the gate as an obstacle rather than as information.
The gate had told us something specific: the small model is fine *except* when it
should be refusing.

**Second decision.** A cascade. The small model answers; if the answer contains a
monetary amount that is not in the service directory, the request is re-asked on
the flagship. The escalation signal is
`murshid.pipeline.groundedness.unsupported_amounts` — the same deterministic check
the harness gates on, which means the cascade escalates on exactly the condition
the gate would have failed on.

**Result.** The suite returned to baseline on every slice, safety at 100%, and the
cost stayed at 0.37 halalas per conversation — because on this traffic the cascade
escalated **zero times**. Its insurance premium was nothing, and it is the reason
the routing table shipped at all.

**The transferable part:** a cascade needs an escalation signal that is cheap,
deterministic, and correlated with being wrong. We rejected model self-assessment
("was that hard?") for the reason Module 6 gives — it is weak and sycophantic. A
schema-validation failure or a groundedness check is a real signal. A model's
opinion of itself is not.

### The semantic cache threshold, which we deliberately did not lower

The replay's closest non-hits sat at 0.918, 0.909 and 0.908 — real traffic just
under the Arabic threshold of 0.92. Lowering it to 0.90 would have converted them
into cache hits and left 0.03 of margin above the worst near-miss pair (0.871,
"my commercial record" versus "my son's commercial record").

We kept 0.92. For a government assistant a wrong hit is not a slightly worse
answer; it is one citizen's answer served to another. Three percentage points of
hit rate does not buy that.

The measurement that shaped this is worth keeping: **Arabic needs a higher
threshold than English, not a lower one.** Arabic spelling variants of the same
question score around 0.94 while English paraphrases score around 0.87, so Arabic
sits closer to its own near-misses. Nobody would have guessed that; the near-miss
suite measured it.

### The Arabic token premium, which turned out to be stale

The instructor material — and most course handouts on this subject — says Arabic
costs 1.5–2.5× its English equivalent in tokens. We measured it across 100
parallel sentence pairs before writing it into a budget:

- on `cl100k_base` (the GPT-4 / GPT-3.5 vocabulary): **2.32×**, as advertised;
- on `o200k_base` (GPT-4o era onward): **0.98×**.

The premium is a property of the tokenizer generation, not of the language, and it
largely disappeared between two vocabularies. We changed the lesson from "Arabic
costs about twice as much" to "count with the route's own tokenizer, and re-measure
when the route changes" — which was always the real rule underneath.

## Things we know are wrong, and are living with

- **The judge shares a model family with the model under test.** That is the
  self-preference conflict named in Module 5. It is reported in
  `EVALUATION_REPORT.md` rather than resolved, because resolving it needs a second
  provider and the honest thing meanwhile is to say so.
- **126 golden cases is small.** Enough to catch the regressions this system
  seeds, not enough to resolve a two-point difference. Every quoted delta below
  about five points should be read as noise until the set grows.
- **Semantic caching is on a hashed n-gram embedding.** Its similarity scale is
  not a production scale. The near-miss suite transfers; the numbers do not.

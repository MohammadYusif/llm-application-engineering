# Murshid — benchmarks

Every number here was produced by a command in this repository, against the course
gateway (`infra/mockgw`) at `MOCKGW_SPEED=0.2`. Reproduce any row by running the
command above it.

**Read the caveat before quoting a figure.** The gateway is a deterministic
simulator, not a model. Latency is compressed, and quality differences between
"model tiers" are rules rather than capability. What these numbers *do* measure
honestly: token accounting, prompt-cache behaviour, guard effectiveness, retrieval
grounding, the meter, and every gate in the pipeline. Point a route at a real
provider (two environment variables, no code change) and re-run the same commands
when you need evidence about a model.

---

## Module 2 — provider comparison

```bash
make bench     # 20 bilingual prompts x 4 routes
```

| Route | p50 | p95 | p50 (ar) | p50 (en) | ar/en input tokens | halalas/call | Residency |
|---|---|---|---|---|---|---|---|
| primary (commercial flagship) | 103 ms | 115 ms | 108 ms | 99 ms | 1.16 | 0.954 | cloud |
| cheap (commercial small) | 50 ms | 54 ms | 53 ms | 47 ms | 1.16 | 0.041 | cloud |
| comparison (Anthropic dialect) | 121 ms | 167 ms | 127 ms | 117 ms | 1.16 | 1.241 | cloud |
| vllm (open-weight, on-prem) | 109 ms | 117 ms | 113 ms | 107 ms | 1.16 | 0.301 | **on-premise** |

**Default route recommendation.** `cheap` for FAQ traffic, `primary` for the
service workflow, `vllm` for anything a data classification pins on-premise. The
routing table in `configs/murshid.yaml` encodes exactly that, and Module 6's gate
is what allowed it to ship.

### The Arabic token premium, measured

```bash
make token-report      # 100 parallel AR/EN sentence pairs
```

| Encoding | English tokens | Arabic tokens | ar/en | chars/token (en) | chars/token (ar) |
|---|---|---|---|---|---|
| `cl100k_base` (GPT-4 / GPT-3.5 era) | 1022 | 2373 | **2.32×** | 5.05 | 1.38 |
| `o200k_base` (GPT-4o era onward) | 1022 | 1005 | **0.98×** | 5.05 | 3.26 |

The premium is a property of the tokenizer generation, not of Arabic. Course
handouts have quoted "1.5–2.5×" for years; on a current vocabulary the same corpus
costs *slightly less* in Arabic than in English. This is why the rule is **count
with the route's own tokenizer**, and why `murshid.llm.tokens` maps model ids to
encodings rather than assuming one.

---

## Module 3 — structured extraction

```bash
make extract-audit                 # default route
make extract-audit ROUTE=vllm      # the open-weight comparison
make extract-audit ROUTE=cheap
```

| Route | First-try pass | After one repair | Escalated | ar (first → after) | en (first → after) |
|---|---|---|---|---|---|
| primary (flagship) | 90% (45/50) | 96% (48/50) | 2 | 91% → 97% | 86% → 93% |
| vllm (open-weight) | 84% (42/50) | 98% (49/50) | 1 | 80% → 97% | 93% → 100% |
| cheap (small) | 74% (37/50) | 98% (49/50) | 1 | 77% → 97% | 64% → 100% |

Invented-field audit: **0 invented fields** across the 15 annotated cases on every
route.

Two things to notice, and one not to over-read:

- **the repair loop closes most of the language gap.** The cheap model's English
  first-try rate is 64%; after one feedback repair it is 100%. That single
  observation justifies the loop better than any slide.
- **the escalation path is exercised.** One or two cases per run fail twice and go
  to human review by design. A corpus where nothing ever escalates is not testing
  the failure path.
- **do not over-read the ordering.** 50 cases carry roughly ±6 points of noise, so
  "vllm beat flagship after repair" is not a finding, it is a coin. Report the
  interval or report nothing.

---

## Module 4 — guards, as a pair of numbers

```bash
make guard-eval
make guard-eval ARGS=--no-classifier    # layer one alone
make leak-attack
```

| Guard configuration | Attack block rate | Legitimate FP rate | Added latency (p50) |
|---|---|---|---|
| Deterministic layer only | 85% (34/40) | 0% | +0.1 ms |
| + PII masking | 85% | 0% | +0.1 ms |
| + cheap-model classifier | **100% (40/40)** | **0% (0/60)** | +35 ms |

System-prompt extraction: 4/5 attempts refused at the input wall, **canary intact
on 5/5** — the fifth is answered normally, which is the attack failing rather than
the guard failing.

The two attacks recorded as misses during Lab 4 (an Arabic authority claim and a
zero-width-separated payload) are fixed in `match_variants` and the constraints
pattern, and both are permanent safety cases in the golden set.

---

## Module 5 — the harness

```bash
make eval && make eval-vllm && make eval-cheap
make calibrate
make gate
```

| Backend | Cases | Overall | ar | en | safety | faq | service | Cost |
|---|---|---|---|---|---|---|---|---|
| primary (flagship) | 126 | **100%** | 100% | 100% | 100% | 100% | 100% | 65.0 hal |
| cheap (small) | 126 | 95% | 95% | 95% | 100% | 94% | 83% | 2.7 hal |
| vllm (open-weight) | 126 | 94% | 92% | 95% | 100% | 92% | 75% | 26.0 hal |

Safety is 100% on every backend, because the safety stratum tests *the guards*,
which are application code — not the model's goodwill. That is the point.

### Judge calibration

| Rubric | Agreement | Cohen's κ | Verdict |
|---|---|---|---|
| `groundedness.v1.md` (unanchored) | 62% | **0.35** | not qualified — do not wire this to anything |
| `groundedness.v2.md` (anchored, evidence required, don't-know clause) | 90% | **0.84** | may gate as a tracking metric |

The difference between the two rows is a rubric edit and nothing else. Four
residual disagreements remain, all on answers whose fee is "No fee" — the rubric
still does not say what to do when there is no number to check. That is what a v3
would fix.

### The gate, demonstrated

```bash
MURSHID_FAQ_PROMPT=answer_faq.v6 make eval LABEL=seeded && make gate LABEL=seeded
```

`answer_faq.v6` is friendlier, and quietly drops the don't-know rule:

```
BLOCKED:
  overall: 89% vs baseline 95% (-6.3pt, margin 2pt)
  slice:intent=faq: 80% vs baseline 92% (-12.5pt, margin 3pt)
  slice:difficulty=hard: 87% vs baseline 99% (-11.3pt, margin 3pt)
```

Code review sees a tone change. The gate sees eight invented fees.

---

## Module 6 — cost and latency

```bash
make replay-before                                   # the baseline
make replay LABEL=s1-prefix
make replay LABEL=s2-cache CACHE=1 SEMANTIC=1
make replay-after                                    # everything on
```

200 conversations, intent-weighted 70/25/5, 566 turns.

| Configuration | Cost/conversation | Δ | p50 turn | p95 conversation | Prompt cache | Eval verdict |
|---|---|---|---|---|---|---|
| Baseline (`answer_faq.v4`) | 4.07 hal | — | 181 ms | 1152 ms | 55% | green (baseline) |
| + prompt-cache discipline (`v5`) | 2.98 hal | −27% | 178 ms | 1102 ms | 72% | green (±0) |
| + response cache (exact + semantic) | 1.66 hal | −59% | 134 ms | 833 ms | 66% | green, wrong hits 0/12 |
| + routing table | 0.37 hal | −91% | 121 ms | 684 ms | 65% | **BLOCKED** (faq −6pt, ar −5pt, hard −6pt) |
| + routing **and cascade** | **0.37 hal** | **−91%** | 122 ms | 687 ms | 65% | green (±0, safety 100%) |

The last two rows are the lesson, and they cost the same. The first routing table
did not survive the gate: sending FAQ traffic to the small model saved 91% and
started guessing fees on out-of-directory questions. The correction was not "move the intent up a tier and
give the saving back" — it was a **cascade** with a deterministic escalation
signal (`murshid.pipeline.groundedness.unsupported_amounts`, the same check the
eval harness gates on). On this traffic the cascade escalated **0 times**: its
insurance premium was nothing, and it is what let the routing table ship.

Where the money went, before anything was touched:

```
by intent: faq 92% | service 6% | guard 1% | router 1%
by stage:  faq_handler 752.4 | service_workflow 45.9 | input_guard 8.7 | router 7.4
```

### The semantic cache

```bash
make eval-cache
python scripts/eval_cache.py --threshold 0.85 --threshold-ar 0.85
```

| Thresholds | Wrong hits (12 near-miss pairs) | Semantic hits on the replay |
|---|---|---|
| en 0.90 / ar 0.92 (shipped) | **0/12** | 2 |
| en 0.85 / ar 0.85 | 1/12 | more |
| en 0.75 / ar 0.75 | 5/12 | more still |

The closest non-hits on the replay were 0.918, 0.909, 0.908 — real traffic sitting
just under the line. Dropping Arabic to 0.90 would convert them into hits and leave
0.03 of margin above the worst near-miss (0.871). For a government assistant, that
margin is the whole argument, and we did not take it.

**Arabic needs a higher threshold than English, not a lower one.** Arabic spelling
variants of the *same* question score ~0.94 while English paraphrases score ~0.87,
so Arabic sits closer to its own near-misses. That asymmetry was measured, not
assumed, and it is why the threshold is per-language.

### Self-host break-even

```bash
make breakeven      # or: python scripts/breakeven.py --tokens-per-sec 950
```

At SAR 12/GPU-hour, 950 tok/s measured, and a 1.35× ops overhead:

| Compared against | Crossover |
|---|---|
| the flagship tier (20.25 SAR/Mtok) | ~25% sustained utilisation |
| the cheap tier (0.90 SAR/Mtok) | never |

Both lines matter. Self-hosting a 7B never beats a small hosted model on price,
which is the honest answer for the 70% of traffic that is FAQ. Against the
flagship tier — what residency-bound traffic would otherwise have to use — it wins
above roughly a quarter utilisation. The recommendation this supports is a routing
table, not a migration.

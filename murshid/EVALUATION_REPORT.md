# Murshid — evaluation report

Generated 2026-09-05 by `python eval/report.py`.

> **Read this first.** Every number below was measured against the course gateway (`infra/mockgw`), which is a deterministic simulator, not a model. The measurements are true statements about this application's harness, guards, meter and gate. They are not evidence about any model's quality. Point a route at a real provider — two environment variables, no code change — and re-run the same harness when you need that kind of evidence.

## 1. Quality — golden set through the real pipeline

| Backend | Cases | Overall | ar | en | safety | wall | cost |
|---|---|---|---|---|---|---|---|
| primary (commercial) | 126 | 100% | 100% | 100% | 100% | 14.1s | 65.0 hal |
| on-prem (vLLM route) | 126 | 94% | 92% | 95% | 100% | 24.5s | 26.0 hal |
| cheap (small model) | 126 | 95% | 95% | 95% | 100% | 10.3s | 2.9 hal |

### Slices — primary (commercial)

| Stratum | Cases | Pass rate |
|---|---|---|
| language = ar | 64 | 100% |
| language = en | 62 | 100% |
| intent = escalate | 8 | 100% |
| intent = faq | 64 | 100% |
| intent = safety | 42 | 100% |
| intent = service | 12 | 100% |
| difficulty = hard | 71 | 100% |
| difficulty = routine | 55 | 100% |
| risk = false_positive | 10 | 100% |
| risk = normal | 74 | 100% |
| risk = safety | 42 | 100% |

Averages are reported last on purpose. A change that lifts the overall number while dropping one stratum is a regression, and the gate reads the slices for exactly that reason.

## 2. Judge calibration

| Rubric | Cases | Agreement | Cohen's kappa | Verdict |
|---|---|---|---|---|
| `groundedness.v1.md` | 40 | 62% | 0.35 | NOT qualified |
| `groundedness.v2.md` | 40 | 90% | 0.84 | may gate (tracking) |

The judge is an instrument and it is qualified, not consulted. It contributes tracking signal only: no safety assertion in this suite depends on a model's opinion.

4 residual disagreements against the sharpened rubric. They are informative rather than embarrassing — read them before writing the next rubric version.

## 3. Safety

- Attack corpus: **40/40 blocked (100%)**, by layer {'deterministic': 34, 'classifier': 6}.
- Legitimate corpus: **false-positive rate 0%** (0/60). Both numbers, always, together — either one alone can be gamed into a broken product.
- Guard latency: {'deterministic': 0.05, 'classifier': 38.5, 'pii': 0.01} (milliseconds, by layer).
- System-prompt extraction: 4/5 refused at the input wall, canary leaked **0** times.
- Semantic cache near-miss suite: **0/12 wrong hits** at thresholds en 0.9 / ar 0.92.

## 4. Cost and latency

| Configuration | Cost/conversation | Δ | p50 turn | p95 conversation | Prompt cache |
|---|---|---|---|---|---|
| Baseline (`answer_faq.v4`, no cache, no routing) | 4.07 hal | +0% | 181 ms | 1152 ms | 55% |
| + prompt-cache discipline (`answer_faq.v5`) | 2.98 hal | -27% | 178 ms | 1102 ms | 72% |
| + response cache (exact + semantic) | 1.66 hal | -59% | 134 ms | 833 ms | 66% |
| + routing table | 0.37 hal | -91% | 121 ms | 684 ms | 66% |

Every row was taken with the eval suite green, and the row that was not is not in the table. Never trade quality you are not measuring for cost you are.

## 5. Known limitations

- **The gateway is a simulator.** Quality differences between the model tiers here are rules, not capability. Every quality claim in this report is a claim about the harness working, not about a model.
- **The semantic cache's embedding is a hashed character n-gram**, not a sentence embedding. Its similarity scale is not a production scale: the threshold that is safe here is not transferable, and the near-miss suite is how you would find your own.
- **The golden set is 126 cases.** That is enough to catch the regressions this course seeds and not enough to resolve a two-point difference. Error bars on a 50-case corpus are wider than most of the deltas people quote from one.
- **The judge shares a family with the model under test** in the default configuration, which is exactly the self-preference conflict the module warns about. Reported as a conflict rather than resolved.
- **Latency figures are compressed** by `MOCKGW_SPEED`. Relative ordering between routes is meaningful; absolute milliseconds are not.


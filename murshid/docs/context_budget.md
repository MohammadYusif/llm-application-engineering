# The context budget

Lab 1 task 5. Not an afterthought: history plus system prompt plus retrieved
content plus tool schemas plus output must fit the window, and **cost scales with
all of it on every turn**. A budget written down is a design artefact; a budget
discovered in production is an incident.

## Murshid's allocation, 16k-token request budget

| Line | Budget | Measured (en / ar) | Why this number |
|---|---|---|---|
| System prompt (`answer_faq.v5`) | 400 | 250 / 250 | Versioned and immutable, so it is byte-stable and the provider caches it. Growth here is a prompt PR, not a surprise. |
| Service directory (trusted context) | 2,500 | 1,127 / 1,352 | The whole directory travels on every FAQ request. It is the cheapest place to be generous *because* it caches; it would be the most expensive if it did not. |
| Tool schemas (service route only) | 900 | 539 | Three tools, one per risk class. Every tool added is paid for on every turn of that route, forever. |
| Windowed history (8 turns) | 4,800 | ~2,900 at turn 8 | The cap is the point: 600 tokens per turn × 8. Unbounded history costs linearly per turn and then overflows for your most engaged users first. |
| This turn's citizen message | 1,000 | ~40 typical, 480 for the 400-word ramble | The cap is enforced by the guard's `max_input_chars`, not hoped for. |
| Output (`max_tokens`) | 700 | ~150 typical | Always bounded. `finish_reason: length` is a correctness bug, and it is logged as one. |
| **Total, FAQ route** | **9,400** | **~1,900 typical, ~5,000 worst case** | Roughly 40% headroom against a 16k window at worst case. |

Measure your own with:

```bash
python -c "import sys; sys.path.insert(0,'src'); \
from murshid.domain.directory import rendered_directory; from murshid.llm.tokens import count; \
print({lang: count(rendered_directory(lang)) for lang in ('en','ar')})"
```

## What the budget forces

**Windowing, not summarisation, for this product.** At ~600 tokens/turn, unbounded
history crosses a 32k window somewhere around turn 50 and a 16k window around turn
23 — and it costs linearly the whole way up. Windowing at 8 turns keeps the
per-turn cost flat. Summarisation (a cheap-model call that compresses older turns)
is the capstone extension: it buys back long-conversation memory at the cost of one
extra call and a new failure mode — a summary that drops the fact the citizen
needed.

**The directory is the budget's biggest line, and its cheapest.** 1,127–1,352
tokens on every FAQ request looks alarming until you notice it is byte-stable and
therefore cached: after the first request in a language it bills at roughly a tenth
of the rate. This is the whole argument for prefix discipline — the *same* content
in the volatile zone would cost ten times as much.

**Arabic is not the problem people expect.** On the current tokenizer the Arabic
directory is 1,352 tokens against English's 1,127 — a 20% premium, not the 2×
figure that has been in course handouts for years. On the previous tokenizer
generation the same corpus ran 2.3×. Budget per route, with the route's own
tokenizer: `make token-report`.

## The failure this prevents

Branch `sim-context-overflow` in the instructor package: unbounded history, a crash
at turn ~23, in production, for the most engaged users. The forecast is arithmetic
anybody can do in a minute — which is exactly why it is worth doing before the
users do it for you.

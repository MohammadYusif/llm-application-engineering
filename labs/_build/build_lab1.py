import sys
sys.path.insert(0, str(__file__.rsplit("\\", 1)[0]))
from nbbuild import SETUP, build, code, md

cells = [
    md("""
::: {.callout-note appearance="simple"}
**Objective** — walk the layered project, read the `LLMClient` protocol and the
adapter behind it, hold a windowed bilingual conversation from the CLI, and write
the context-budget table.

**Before you start** — `make doctor` all green, and the gateway running
(`make gateway`, or `docker compose up -d gateway`).

**You finish with** — `make chat` working in both languages, a window that
demonstrably forgets, and `docs/context_budget.md` with six justified lines.
:::

Every code cell below runs the same command the Makefile runs, through
`sys.executable` so it works with or without `make`. Run the setup cell first.
"""),
    code(SETUP),

    md("""
## 0 · Five minutes with a demo that works on stage

`demo_v0.py` is sixty lines: hardcoded model name, prompt inline, no timeout, no
state, `print` streaming. It works.

Read it first and list **three defects it ships with** before running it.
"""),
    code('print(pathlib.Path("demo_v0.py").read_text(encoding="utf-8")[:1200])'),

    md("Now run it. The question is the one the demo was built to answer."),
    code('run("demo_v0.py", "How do I renew my commercial licence?")'),

    md("""
::: {.callout-important}
## The directory says SAR 200

The demo invented a fee, fluently, for the exact question it was built to demo —
because its service facts live in a string literal that nothing checks, and it has
no rule about what to do when it does not know.

Nobody notices unless they already know the right answer. That is the failure mode
this entire course is arranged around, and it is on screen in the first ten minutes
of day one.
:::

## 1 · The skeleton (10 min)

The layout is not decoration: it is what makes the CI check in
`tests/test_architecture.py` meaningful. That test walks the AST of everything
under `src/murshid/` and fails if any module outside `llm/` imports `openai` or
`anthropic`.
"""),
    code('run("-m", "pytest", "tests/test_architecture.py", "-q")'),

    md("""
## 2 · The boundary (15 min)

Everything the application is allowed to know about a provider is in
`src/murshid/llm/interfaces.py`. Read the protocol itself — four lines.
"""),
    code('''
import inspect
from murshid.llm.interfaces import LLMClient, LLMRequest, LLMResponse
print(inspect.getsource(LLMClient))
'''),

    md("""
`OpenAICompatClient.complete()` does four things, each of which is a rule from the
theory rather than a detail of the SDK:

1. it resolves `request.model_alias` **through the route config** — never a literal
   model id;
2. it sets `max_tokens`, always;
3. it sets `max_retries=0` on the SDK client, because *we* own retry policy;
4. it returns the **concrete** `model_id` that answered, plus `usage`, plus latency.

Watch all four arrive in one line of output.
"""),
    code('run("-m", "murshid.cli", "ask", "How do I renew my commercial licence?")'),

    md("""
SAR 200 this time, from the directory, because the answer is composed from facts
that arrived in the prompt.

Ask the identical question again and watch `cached` climb — that is Module 6
arriving early, and it is the reason `cache_prefix_messages` exists on a Module 1
type.
"""),
    code('run("-m", "murshid.cli", "ask", "How do I renew my commercial licence?")'),

    md("""
## 3 · Windowed state and the CLI (10 min)

**LLM APIs are stateless.** Every request carries the whole conversation. "Memory"
is an application concern, and `ConversationState` ships with `max_turns=8`.

`make chat` is interactive, so here is the same thing without a terminal: nine
exchanges, then a question about the first one.
"""),
    code('''
from murshid.domain.session import ConversationState

state = ConversationState(max_turns=8)
for i in range(9):
    state.add_user(f"question {i}")
    state.add_assistant(f"answer {i}")

msgs = state.messages()
print(f"window: {len(msgs)} messages, max {state.max_turns} turns")
print("oldest kept:", msgs[0].content)
print("newest kept:", msgs[-1].content)
print("\\nis 'question 0' still in the window?", any("question 0" == m.content for m in msgs))
'''),

    md("""
::: {.callout-important}
## The moment statelessness lands — do not skip it

The window forgot turn 1, on cue. There is nothing wrong. A window is a *decision*
with a cost curve, not an implementation detail — and the alternative, unbounded
history, is a bill that grows every turn until the context overflows for your most
engaged users first.

Pinned by `tests/domain/test_ticket_and_session.py::test_the_window_forgets_the_oldest_turn`.
:::

## 4 · The context budget (10 min)

Write `docs/context_budget.md`: allocate a 16k-token request budget across the
system prompt, the service directory, tool schemas, windowed history, this turn,
and output — and **justify each line**.

Measure rather than guess.
"""),
    code('''
from murshid.domain.directory import rendered_directory
from murshid.llm.tokens import count

for lang in ("en", "ar"):
    print(f"{lang}: {count(rendered_directory(lang))} tokens")
'''),

    md("""
Two questions your document has to answer:

- At ~600 tokens per turn, which turn overflows a 16k window with *unbounded*
  history? Show the arithmetic.
- Which line of your budget is the largest, and is it in the cacheable prefix or the
  volatile tail? Module 6 will make you care.

The reference version is in `docs/context_budget.md`. Compare after you have
written yours, not before.

## 5 · Reliability, under a real fault

The gateway can inject a real outage. This is the drill, end to end: turn it on,
ask a question, watch the retry and the fallback, turn it off.
"""),
    code('print(fault({"mode": "overload", "seconds": 60, "model": "course-flagship"}))'),

    md("Now ask. Keep the log this time — the retry and the failover *are* the lesson."),
    code('run("-m", "murshid.cli", "ask", "How do I renew my commercial licence?", quiet_logs=False)'),

    md("Turn the fault off before moving on."),
    code('print(fault({"mode": "off"}))'),

    md("""
Three things to notice in that log:

1. the retry **honoured the header** rather than guessing a backoff;
2. attempts were **capped** — retries multiply cost and tail latency;
3. the citizen got an answer, from the on-premise route, and never knew.

## 6 · Commit (5 min)

```bash
git add -A
git commit -m "feat: murshid skeleton with provider boundary and windowed state"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `✗ route primary` in `make doctor` | the gateway is not running | `make gateway` in another terminal |
| `AuthenticationError` against a real gateway | `.env` not loaded, or the wrong variable name | `cp configs/settings.example.env .env`; the prefix is `MURSHID_` |
| Responses ignore earlier turns | state not replayed into `messages` | history serialises system first, then turns oldest → newest |
| Arabic renders as boxes | console code page | Windows Terminal or VS Code, and `PYTHONUTF8=1` |
| `finish_reason="length"` mid-sentence | `max_tokens` too low | raise it per your budget — and note that truncation is *silent* |
| Everything is slow (~2 s per call) | `localhost` resolving to IPv6 first | the config uses `127.0.0.1` for exactly this reason |

## If you finish early

Stream the answer instead, and note that TTFT and total are reported separately.
That distinction is tomorrow's warm-up and Module 6's headline.
"""),
    code('run("-m", "murshid.cli", "stream", "What documents do I need to renew my commercial registration?")'),
]

p = build("lab1-skeleton", "Lab 1 — Build the Murshid skeleton",
          "Day 1, hour 3 · 50 minutes · pairs", cells)
print("wrote", p)

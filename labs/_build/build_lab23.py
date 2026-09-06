import sys
sys.path.insert(0, str(__file__.rsplit("\\", 1)[0]))
from nbbuild import SETUP, build, code, md

# ---------------------------------------------------------------- lab 2 -----
lab2 = [
    md("""
::: {.callout-note appearance="simple"}
**Objective** — run the one contract suite against every adapter, serve the
open-weight route with no code change, measure time-to-first-token, survive a live
429 storm, and record the first provider-comparison table.

**Before you start** — Module 1's lab complete. Gateway running.

**You finish with** — contract tests green on every adapter, a fault-drill log
excerpt, and `BENCHMARKS.md` seeded with numbers you produced.
:::
"""),
    code(SETUP),

    md("""
## 1 · The contract suite (12 min)

"Implements the protocol" is a test, not a docstring claim. The same test class is
parametrised over every adapter — and the parametrisation only fills in when the
gateway answers, which is why the count changes with it running.
"""),
    code('run("-m", "pytest", "tests/llm/test_adapter_contract.py", "-v", "--no-header", "-q")'),

    md("""
Four differences between the dialects are load-bearing. Read where each one stops —
this is `AnthropicClient.complete`, and the comment in the middle is the one that
matters most.
"""),
    code('''
import inspect
from murshid.llm.anthropic_client import AnthropicClient
src = inspect.getsource(AnthropicClient.complete)
print(src[:1900])
'''),

    md("""
`temperature` is simply absent — not defaulted, not `None`. The normalised
`LLMRequest` still carries it because the OpenAI dialect still has it; deleting the
field to silence this adapter would be the wrong repair.

## 2 · The open-weight route, with no code change (8 min)

The route already exists in `configs/murshid.yaml`. Read it, then use it.
"""),
    code('''
from murshid.config import get_settings
s = get_settings()
for name, route in s.routes.items():
    print(f"{name:12} {route.base_url:34} residency={route.residency}")
'''),

    code('run("-m", "murshid.cli", "--route", "vllm", "ask", "ما هي خطوات إصدار سجل تجاري؟")'),

    md("""
Note the `model_id`: `murshid-onprem`. **Nothing in `src/` changed.**
`OpenAICompatClient` works unchanged because vLLM speaks the chat-completions
schema, which is the de-facto wire standard.

## 3 · Streaming and time-to-first-token (12 min)

Record **both** numbers. Then answer, in one sentence: does streaming reduce total
latency?
"""),
    code('run("-m", "murshid.cli", "stream", "What documents do I need to renew my commercial registration?")'),

    md("""
It does not. It reduces *perceived* latency. Generation time is unchanged — which
is why Module 6 treats TTFT and generation as two separate levers with two
different fixes.

Without `stream_options={"include_usage": True}` the usage never arrives and the
cost meter silently undercounts most traffic. The contract test asserts the final
frame carries it:
"""),
    code('run("-m", "pytest", "tests/llm/test_adapter_contract.py", "-k", "streaming", "-q", "--no-header")'),

    md("""
## 4 · The fault drill (10 min)

Your instructor may fire this without warning. Fire it yourself here: a 429 storm
with a real `Retry-After` header on the primary model.
"""),
    code('print(fault({"mode": "rate_limit", "seconds": 120, "model": "course-flagship", "retry_after": 2}))'),

    md("Ask, and keep the log — the retry and the failover *are* the lesson."),
    code('run("-m", "murshid.cli", "ask", "كيف أجدد رخصتي التجارية؟", quiet_logs=False)'),

    code('print(fault({"mode": "off"}))'),

    md("""
Three things to notice:

1. the retry **honoured the header** rather than guessing a backoff — `retry_after`
   travelled from the provider's response into `ResilientClient._delay_for`;
2. attempts were **capped** — retries multiply cost and tail latency;
3. the citizen got an answer, from the on-premise route, and never knew.

What the gateway saw:
"""),
    code('''
stats = gateway_stats()
print(json.dumps({k: stats[k] for k in list(stats)[:8]}, indent=2, ensure_ascii=False))
'''),

    md("""
## 5 · The bench table (8 min)

Twenty bilingual prompts against every configured route, then the token report.
"""),
    code('run("scripts/bench_providers.py")'),
    code('run("scripts/token_report.py")'),

    md("""
Commit the table to `BENCHMARKS.md` with **one sentence**: which route would you
make Murshid's default today, and on what evidence? That sentence is the seed of
the capstone's model-comparison criterion.

Then revise whatever you believed about Arabic. The "costs about twice as much"
rule of thumb is a fact about a *tokenizer generation*; on a current vocabulary it
is gone. The rule that survives is the one underneath: count with the route's own
tokenizer.

## If you finish early

Murshid handles 30,000 conversations a day, averaging six turns, roughly 900 input
and 150 output tokens per turn. At the price sheet's rates, what does routing 70%
of turns to the cheap model save per month? Keep your estimate — Module 6's
`make replay-after` will tell you how wrong it was, and in which direction.
"""),
]

# ---------------------------------------------------------------- lab 3 -----
lab3 = [
    md("""
::: {.callout-note appearance="simple"}
**Objective** — Part A: extract validated `ServiceTicket` objects from messy
bilingual citizen messages and measure the schema-pass rate. Part B: wire three
tools and the bounded loop, and pass the negative-test suite.

**Before you start** — Module 2's lab complete. `data/citizen_messages_50.jsonl` —
bilingual and deliberately messy: dialect, missing hamzas, Arabic-Indic digits,
mixed script, one 400-word polite ramble.

**You finish with** — six numbers in `BENCHMARKS.md`, an invented-field audit at
zero, and the tool-safety suite green.
:::
"""),
    code(SETUP),

    md("""
# Part A — the ticket

## 1 · The contract (10 min)

The validators carry the rules no JSON Schema can express. Read both.
"""),
    code('''
import inspect
from murshid.domain.ticket import Applicant
src = inspect.getsource(Applicant)
print(src[src.index("@field_validator"):][:1100])
'''),

    md("""
`if v is None: return v` — absent is legal, *invented* is not, and that distinction
is the never-invent rule expressed in a type. The phone validator normalises before
checking, so `05x xxx xxxx` and `+9665xxxxxxxx` are the same number to this
contract, and its error message names the expected shape because that message is
what the repair turn sees.

Confirm the contract still fits the strict-mode subset:
"""),
    code('run("scripts/schema_check.py")'),

    md("""
## 2 · The repair loop (15 min)

Extraction on a rich message, then on one with almost nothing in it.
"""),
    code('''
from murshid.app import build_client
from murshid.config import get_settings
from murshid.pipeline.extract import extract_ticket

client = build_client(get_settings(), "primary")
ticket, outcome = extract_ticket(
    client, "السلام عليكم، اسمي فيصل العتيبي وأبغى أجدد السجل التجاري حقي في الرياض")
print("first try:", outcome.first_try, "| attempts:", outcome.attempts)
print(ticket.model_dump_json(indent=2)[:700])
'''),

    code('''
ticket2, outcome2 = extract_ticket(client, "كيف أجدد رخصتي التجارية؟")
print("first try:", outcome2.first_try, "| attempts:", outcome2.attempts)
print("national_id:", ticket2.applicant.national_id)
print("phone      :", ticket2.applicant.phone)
print("city       :", ticket2.city)
'''),

    md("""
`None` is the correct answer. `extract_ticket.v3`'s never-invent rule plus its one
null example are what earn it. **An invented field is a defect; an empty one is a
fact.**

## 3 · Measure the corpus (15 min)
"""),
    code('run("scripts/extract_corpus.py", "--audit")'),

    md("""
All six numbers go in `BENCHMARKS.md`. The two escalations are not a bug: one
repair, then a designed hand-off. **A corpus where nothing ever escalates is not
testing the failure path.**

## 4 · The comparison (10 min)
"""),
    code('run("scripts/extract_corpus.py", "--route", "vllm", "--audit")'),

    md("""
::: {.callout-warning}
## Then write a sentence about error bars

Fifty cases carry roughly ±6 points of noise, so a few points between routes after
repair is a coin, not a finding. The differences that *are* real are the first-try
rates and the size of the gap the repair loop closes. Learning which differences
survive their error bars is most of what Module 5 is about.
:::

# Part B — the tool loop

## 5 · Tool descriptions route (10 min)

The smoke suite asserts *which* tools fire, including the cases where none should.
"""),
    code('run("scripts/tool_smoke.py")'),

    md("""
Now break it on purpose. Descriptions route — one over-broad sentence and the tool
fires on everything.

The smoke script has to run **in this kernel** for the edit to take effect, so
import its `main` rather than shelling out: a subprocess would load its own copy of
the registry and the change would vanish.
"""),
    code('''
import importlib, sys
sys.path.insert(0, "scripts")
tool_smoke = importlib.import_module("tool_smoke")

from murshid.tools import registry
tool = registry.BY_NAME["check_application_status"]
original = tool.description
print("before:", original[:100], "...")
'''),
    code('''
tool.description = "Use for any question about applications."
tool_smoke.main()
'''),

    md("""
One over-broad sentence and the documents question now fires the status tool.
**Descriptions route** — which is why the `don't` cases in a description are not
padding.

Put it back before moving on; the rest of the lab depends on it.
"""),
    code('''
tool.description = original
tool_smoke.main()
'''),

    md("""
## 6 · Bounds and the authorisation gate (15 min)

Every negative test exercises `_execute`, where the *order* of the checks is the
security model.
"""),
    code('run("-m", "pytest", "tests/pipeline/test_tool_safety.py", "-v", "--no-header", "-q")'),

    md("""
::: {.callout-important}
## Where else could that identity check live?

List the alternatives before reading on: in the prompt; in the tool description; in
the model's good judgement.

Now ask what happens to each under Module 4's injection scenarios. **Every answer
that lives inside the token stream is an answer an attacker can write to.** The
session object is the only one that is not.
:::

Watch the gate refuse a cross-citizen booking directly.
"""),
    code('''
from murshid.domain.session import Session

s = Session(citizen_id="1012345678", identity_verified=True)
for label, args in [("own account ", {"citizen_id": "1012345678"}),
                    ("someone else", {"citizen_id": "2098765432"})]:
    v = s.authorize("book_appointment", args)
    print(f"{label}: allowed={v.allowed} reason={v.reason}")
    if v.user_hint:
        print(f"              hint: {v.user_hint}")
'''),

    md("""
The argument is *read*, but `self.citizen_id` is what it is compared against, and
the verdict carries a `user_hint` because a refusal a citizen cannot act on is a
dead end rather than a guardrail.

## 7 · End to end (15 min)

A booking, and then the audit trail it left.
"""),
    code('run("-m", "murshid.cli", "ask", "أريد حجز موعد في الأحوال المدنية بالرياض بتاريخ 2026-10-14، أكّد الحجز")'),

    md("""
## 8 · Commit (10 min)

```bash
git commit -am "feat: validated ticket extraction and the bounded tool loop"
```

## If you finish early

Add parallel execution for read-only calls, and prove side-effecting calls still
serialise. Then argue about the fourth risk class: lab results are read-only
*technically* but sensitive. Does the registry need another class, or does
authorisation already cover it?
"""),
]

for name, title, sub, cells in [
    ("lab2-two-providers", "Lab 2 — Two providers, one interface",
     "Day 1, hour 5 · 50 minutes · pairs", lab2),
    ("lab3-tickets-and-tools", "Lab 3 — Structured tickets and the tool loop",
     "Day 2, hours 2 and 4 · 2 × 50 minutes · pairs", lab3),
]:
    print("wrote", build(name, title, sub, "", cells))

"""Lab 1 — Module 1's six points, each demonstrated in code.

One section per numbered section of `modules/m1-architecture.qmd`, in the same
order and the same vocabulary. Each one recaps the point in a sentence or two and
then shows it running against Murshid, the worked example.

The code is written in the cells rather than shelled out to `make`, so a reader
can change a line and see what happens — which is the difference between a lab
that explains and a lab that runs.
"""

from __future__ import annotations

from nbbuild import SETUP, build, code, md

LEAD = """
Module 1 argued for one boundary between the application and the provider, a
pattern chosen on evidence, state you can bound, and reliability policy in a single
place. Every point it made is below, running against **Murshid** — the bilingual
citizen-services assistant this course builds on. Read a cell, run it, change a
value, run it again.

Murshid is the worked example. Your capstone is your own application, on a track
you choose, and the last section hands each of these points back to you for it.
"""

CELLS = [
    md("""
## Setup

One cell. On Colab it fetches the course and starts the gateway; on your own
machine it finds the project you already have and checks the gateway is up.
"""),
    code(SETUP),

    md("""
## 1. LLM applications fail quietly

A web service that breaks returns a 500 and wakes someone. An LLM application that
breaks returns a fluent, confident, wrong answer, and nobody is woken — the fee is
plausible, the format is right, and the citizen acts on it.

The service directory is the ground truth here. `unsupported_amounts()` compares
every number in an answer against the numbers the directory actually contains, so
"quietly wrong" becomes something a machine can see.
"""),
    code('''
from murshid.domain.directory import rendered_directory
from murshid.pipeline.groundedness import is_grounded, unsupported_amounts

directory = rendered_directory("en")
print("the directory the model is given:", len(directory), "characters")
for line in directory.splitlines():
    if "fee:" in line:
        print("  ", line.strip())
'''),

    md("""
Now an answer that *reads* perfectly and is wrong in the one place that matters.
Nothing about its shape gives it away — only the comparison does.
"""),
    code('''
plausible = ("Renewing a commercial registration costs SAR 750 per year "
             "and is issued within two working days.")

print("answer:", plausible)
print("amounts with no support in the directory:", unsupported_amounts(plausible, directory))
print("grounded?", is_grounded(plausible, directory))
'''),

    md("""
That comparison is a **deterministic check**: no model, no judgement, no cost. It
is the cheapest thing in Module 5's harness and it catches the failure that a
demo never shows you. Note what it does *not* do — it says nothing about tone,
helpfulness or completeness. One check, one claim.
"""),

    md("""
## 2. Four patterns, as an escalation ladder

A single call, a workflow, a router, a bounded agentic loop — in that order, and
you climb only when the traffic forces you to. Murshid is a **router**: it
classifies each message into an intent and hands it to the handler for that
intent, because its traffic really does split into questions and transactions.

Classification is itself a small model call, on the cheap route.
"""),
    code('''
from murshid.app import build_client
from murshid.config import get_settings
from murshid.pipeline.router import IntentRouter

settings = get_settings()
router = IntentRouter(build_client(settings, settings.cheap_route))

for message in ["How much is a commercial licence renewal?",
                "Book me an appointment in Jeddah next Tuesday",
                "كم رسوم تجديد السجل التجاري؟",
                "My application REF-2291 has been stuck for three weeks"]:
    print(f"{router.classify(message):<10} <- {message}")
'''),

    md("""
Two of those are questions and two are transactions, in two languages, and the
router separates them before any expensive work happens. That is the whole
argument for the pattern: the cheap path stays cheap, and only the traffic that
needs tools pays for tools.
"""),

    md("""
## 3. The model boundary

One interface. The application depends on `LLMClient`, and every provider is an
implementation of it. The request and the response are the course's own types, so
nothing above the boundary ever sees a provider's field names.
"""),
    code('''
from murshid.llm.interfaces import LLMRequest, LLMResponse, Message

print("LLMRequest  :", ", ".join(LLMRequest.model_fields))
print("LLMResponse :", ", ".join(LLMResponse.model_fields))
'''),

    md("""
`usage`, `model_id` and `finish_reason` are on the response because control flow
depends on them: the cost meter needs the first two, and the tool loop branches on
the third. A boundary that returns only text throws that away and every layer
above has to guess.

The third implementation is the one you feel first — a fake, scripted in a line,
that needs no network and no key.
"""),
    code('''
from murshid.llm.fake import FakeClient

fake = FakeClient(model_id="demo-model").script_text("SAR 200 per year.", tokens=(120, 9))
reply = fake.complete(LLMRequest(
    messages=[Message(role="user", content="Licence renewal fee?")], max_tokens=64))

print(type(reply).__name__, "->", reply.text)
print("model_id:", reply.model_id, "| finish:", reply.finish_reason,
      "| tokens in/out:", reply.usage.input_tokens, "/", reply.usage.output_tokens)
'''),

    md("""
Now the same request against a live route on the course gateway. Different
implementation, different model, **same two lines of calling code** — that is the
claim the boundary makes, and it is either true in your code or it is a diagram.
"""),
    code('''
live = build_client(settings, settings.primary_route)
answer = live.complete(LLMRequest(
    messages=[Message(role="system", content="Answer only from this directory.\\n" + directory),
              Message(role="user", content="How much does a commercial licence renewal cost?")],
    model_alias="murshid-flagship", max_tokens=200))

print(answer.text.strip())
print()
print("model_id:", answer.model_id, "| route:", answer.route,
      "| usage:", answer.usage.model_dump())
'''),

    md("""
Two things worth noticing before moving on. The answer is **grounded in the
directory that arrived in the prompt** — take the directory away and the same
question cannot be answered. And `usage` came back populated, which is what makes
Module 6's cost meter possible at all.
"""),
    code('''
print("grounded?", is_grounded(answer.text, directory))
'''),

    md("""
The architecture test is what keeps the boundary honest. It fails the build if
`openai` or `anthropic` is imported anywhere except the two adapter files.
"""),
    code('''
run("-m", "pytest", "tests/test_architecture.py")
'''),

    md("""
## 4. State, streaming, and the sync/batch line

The model is stateless. Every turn resends the whole history, so "memory" is a
decision your application makes and pays for. Murshid's default is a **window**:
keep the last N turns, drop the rest.
"""),
    code('''
from murshid.domain.session import ConversationState

state = ConversationState(max_turns=2)   # small, so the effect is visible
for i in range(1, 4):
    state.add_user(f"question {i}")
    state.add_assistant(f"answer {i}")

print("turns kept:", [m.content for m in state.turns])
print("is 'question 1' still in the window?",
      any(m.content == "question 1" for m in state.turns))
'''),

    md("""
Turn 1 is gone, on cue. Nothing is broken — a window is a *decision with a cost
curve*, and the alternative, unbounded history, is a bill that grows every turn
until the context overflows for your most engaged users first.

What `messages()` sends is the system prompt plus that window, rebuilt each turn.
"""),
    code('''
sent = state.messages(system="You are Murshid.")
for m in sent:
    print(f"{m.role:<9} {m.content[:60]}")
print()
print("messages on the wire this turn:", len(sent))
'''),

    md("""
Streaming changes the *perceived* latency, not the total. The number that matters
is time-to-first-token: the wait before anything appears on screen.
"""),
    code('''
import time

start = time.perf_counter()
ttft, chunks = None, 0
for chunk in live.stream(LLMRequest(
        messages=[Message(role="system", content=directory),
                  Message(role="user", content="What documents do I need to renew a licence?")],
        model_alias="murshid-flagship", max_tokens=160)):
    if chunk.delta and ttft is None:
        ttft = (time.perf_counter() - start) * 1000
    chunks += 1
total = (time.perf_counter() - start) * 1000

print(f"chunks: {chunks}   time to first token: {ttft:.0f} ms   total: {total:.0f} ms")
print(f"the reader waits {ttft:.0f} ms instead of {total:.0f} ms — the same work, felt differently")
'''),

    md("""
## 5. Reliability lives at the boundary, once

Timeouts, retries with jitter, and failover belong in one place. Put them in each
call site and you get four different policies, three of which are wrong, and a
retry storm the first time a provider is slow rather than down.

`FakeClient` can script a rate limit, so the policy can be tested without waiting
for a real one.
"""),
    code('''
from murshid.llm.resilient import ResilientClient

flaky = FakeClient(model_id="primary-model").script_rate_limit(times=2)
flaky.script_text("Answered after two 429s.", tokens=(80, 12))

# The chain is a list of named hops; sleep is injected so the lab does not
# actually wait out the backoff.
client = ResilientClient([("primary", flaky)], max_attempts=3, sleep=lambda _: None)
out = client.complete(LLMRequest(messages=[Message(role="user", content="hello")], max_tokens=64))

print("text:", out.text)
print("calls the primary actually took:", flaky.call_count)
'''),

    md("""
Two 429s, one answer, and the calling code never knew. Now the case retries cannot
fix — the primary is *down*, not busy — where the second route earns its keep.
"""),
    code('''
from murshid.llm.interfaces import LLMError

dead = FakeClient(model_id="primary-model")
dead.script_error(LLMError("connection refused"), times=3)
spare = FakeClient(model_id="fallback-model").script_text("Served by the fallback route.")

client = ResilientClient([("primary", dead), ("on_prem", spare)],
                         max_attempts=2, sleep=lambda _: None)
out = client.complete(LLMRequest(messages=[Message(role="user", content="hello")], max_tokens=64))

print("text:", out.text)
print("answered by:", out.model_id)
'''),

    md("""
And when every hop is exhausted, the application still owes the citizen a sentence
rather than a stack trace. A degraded reply is a product decision, made in advance.
"""),
    code('''
from murshid.llm.resilient import degraded_response

for language in ("en", "ar"):
    print(language, "->", degraded_response(language).text)
'''),

    md("""
## 6. Common mistakes

Module 1 listed six. Three of them are visible in the cells above:

- **calling the SDK from the handler** — then a provider change is a rewrite, and
  the architecture test above is what stops it happening by accident;
- **unbounded history** — the window is a decision; make it deliberately and
  measure what it costs;
- **retry logic per call site** — one policy, at the boundary, tested against a
  scripted 429 rather than hoped for.

The other three are cheaper to fix now than in week three: no `usage` on the
response, no timeout on the client, and a demo whose numbers nobody can reproduce.
"""),

    md("""
## Your turn — on your own project

Everything above ran against Murshid. Your capstone is **your** application, on the
track you pick, and it needs the same four things from this module. Start them now
rather than on Day 4:

1. **Name the shape.** Which of the four patterns does your traffic want — a single
   call, a workflow, a router, or a bounded agentic loop? One paragraph justifying
   it against the traffic mix you expect. That paragraph is your first ADR.
2. **Draw the boundary before you write an adapter.** One interface, a normalised
   request and response carrying `model_id`, `usage` and a finish reason. The shape
   in `src/murshid/llm/interfaces.py` is there to copy.
3. **Decide your state strategy** and say what it costs. Windowed is the safe
   default; if you pick summarisation, you owe the eval cases showing a long
   conversation still remembers what matters.
4. **Write your own context budget** — your directory, your tool schemas, your
   history. Measure the numbers rather than guessing them.

**Next:** [Module 2 — APIs and open weights](../modules/m2-apis-and-open-weights.qmd),
then [Lab 2](lab2-two-providers.ipynb).
"""),
]

if __name__ == "__main__":
    print("wrote", build("lab1-skeleton", "Lab 1 — the model boundary, in code",
                         "Day 1 · after Module 1", LEAD, CELLS))

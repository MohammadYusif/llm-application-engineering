"""Lab 2 — Module 2's points, each demonstrated in code.

One section per numbered section of `modules/m2-apis-and-open-weights.qmd`. The
two dialects, tokenizers, the error taxonomy and the open-weight route are all
shown running rather than described, against Murshid and the course gateway.
"""

from __future__ import annotations

from nbbuild import SETUP, build, code, md

LEAD = """
Module 2 covered the two wire dialects behind one interface, tokens counted per
route, the error taxonomy that decides whether to retry, and an open-weight model
served with no change above the boundary. Each of those is below, running against
**Murshid**.

The course gateway speaks both dialects, so you can watch the translation happen
without a key to either provider.
"""

CELLS = [
    md("""
## Setup
"""),
    code(SETUP),

    md("""
## 1. Two wire dialects

The same conversation goes over the wire two different ways. OpenAI-compatible
APIs take a flat `messages` list with the system prompt as the first message.
Anthropic takes `system` as a **separate top-level field** and content as typed
blocks — so the adapter has to split them.
"""),
    code('''
from murshid.llm.anthropic_client import split_system, to_anthropic_tools
from murshid.llm.interfaces import Message

conversation = [Message(role="system", content="You are Murshid, a services assistant."),
                Message(role="user", content="How much is a licence renewal?")]

system, body = split_system(conversation)
print("openai   : messages =", [m.role for m in conversation])
print("anthropic: system   =", repr(system))
print("           messages =", body)
'''),

    md("""
Tools are declared differently too. OpenAI wraps each one in `{"type": "function",
"function": {...}}` with `parameters`; Anthropic takes the tool flat with
`input_schema`. Same JSON Schema, two envelopes.
"""),
    code('''
from murshid.tools.registry import tool_schemas

openai_tool = tool_schemas(["check_application_status"])[0]
anthropic_tool = to_anthropic_tools([openai_tool])[0]

print("openai   :", list(openai_tool), "->", list(openai_tool["function"]))
print("anthropic:", list(anthropic_tool))
print()
print("the schema itself is unchanged:",
      openai_tool["function"]["parameters"] == anthropic_tool["input_schema"])
'''),

    md("""
Above the boundary none of that is visible. The same `LLMRequest` goes to both
routes and comes back as the same `LLMResponse` — only `model_id` differs.
"""),
    code('''
from murshid.app import build_client
from murshid.config import get_settings
from murshid.llm.interfaces import LLMRequest

from murshid.domain.directory import rendered_directory

settings = get_settings()

# Same grounded question as Lab 1: the directory goes in the system message, so an
# answer that quotes a fee is quoting one that exists.
directory = rendered_directory("en")
question = [Message(role="system", content="Answer only from this directory.\\n" + directory),
            Message(role="user", content="How much does a commercial licence renewal cost?")]

for route in ("primary", "comparison"):
    client = build_client(settings, route)
    reply = client.complete(LLMRequest(messages=question, model_alias="murshid-flagship",
                                       max_tokens=260))
    print(f"{route:<11} dialect={settings.route(route).dialect:<10} "
          f"model_id={reply.model_id:<17} finish={reply.finish_reason}")
    print(f"            {reply.text.strip().splitlines()[1][:88]}")
'''),

    md("""
Two dialects, one call site. That is the whole argument for the adapter, and the
architecture test from Lab 1 is what stops the provider SDK leaking past it.
"""),

    md("""
## 2. Sampling, determinism, and tokens

Temperature is a sampling parameter, not a truth dial. Even at `temperature=0` a
real provider can vary between calls — batching, hardware and model updates all
move the result — so an application that needs stability gets it from **structure**
(schemas, validators, tests) rather than from a hyperparameter.
"""),
    code('''
client = build_client(settings, settings.primary_route)
answers = [client.complete(LLMRequest(messages=question, model_alias="murshid-flagship",
                                      temperature=0.0, max_tokens=120)).text
           for _ in range(3)]

print("three calls at temperature 0 identical?", len(set(answers)) == 1)
print()
print("On this gateway they are, because it answers from rules. Against a real")
print("provider, do not assume it — the module explains why, and Module 5 is how")
print("you would find out.")
'''),

    md("""
Tokens are not words, and the count depends on the tokenizer the route uses. The
same two sentences, counted under two encodings, is where the Arabic premium
becomes visible.
"""),
    code('''
from murshid.llm import tokens

en = "How much does it cost to renew a commercial registration?"
ar = "كم تبلغ رسوم تجديد السجل التجاري؟"

print(f"{'encoding':<14}{'english':>9}{'arabic':>9}   ratio")
for encoding in ("o200k_base", "cl100k_base"):
    e, a = tokens.count_with(en, encoding), tokens.count_with(ar, encoding)
    print(f"{encoding:<14}{e:>9}{a:>9}   {a / e:.2f}x")

print()
print("route encodings:",
      {m: tokens.encoding_for_model(m) for m in ("course-flagship", "murshid-onprem")})
'''),

    md("""
Under `cl100k_base` the Arabic sentence costs more than twice its English
counterpart; under `o200k_base` it does not. Same text, same meaning — the bill
depends on which route it went to. Count per route, on your own corpus, before
quoting anyone a price.
"""),

    md("""
## 3. Streaming, rate limits, and the error taxonomy

Streaming buys perceived latency. The number to report is time-to-first-token,
alongside the total — one without the other hides the trade.
"""),
    code('''
import time

start = time.perf_counter()
ttft, chunks, text = None, 0, []
for chunk in client.stream(LLMRequest(messages=question, model_alias="murshid-flagship",
                                      max_tokens=200)):
    if chunk.delta:
        if ttft is None:
            ttft = (time.perf_counter() - start) * 1000
        text.append(chunk.delta)
    chunks += 1
total = (time.perf_counter() - start) * 1000

print(f"chunks {chunks} | first token {ttft:.0f} ms | complete {total:.0f} ms")
print("".join(text).strip().splitlines()[1][:88])
'''),

    md("""
Now a real rate limit. The gateway has a fault injector, so the 429 is served over
the wire rather than faked in Python — the adapter's error mapping runs for real.
"""),
    code('''
from murshid.llm.interfaces import LLMError

print(fault({"mode": "rate_limit", "seconds": 20, "retry_after": 2}))

try:
    client.complete(LLMRequest(messages=question, model_alias="murshid-flagship", max_tokens=60))
except LLMError as exc:
    print()
    print("class     :", type(exc).__name__)
    print("status    :", exc.status)
    print("retryable :", exc.retryable)
    print("retry_after:", exc.retry_after, "seconds — the server said when, so honour it")
'''),

    md("""
`retryable` is the whole taxonomy in one flag. 429 and 5xx are retryable with
backoff; 400, 401 and a context-length error are not, and retrying them just burns
quota and time. Anything the adapter does not recognise is **not** retryable —
guessing wrong in that direction is cheaper.

The resilient client reads that flag and nothing else.
"""),
    code('''
from murshid.llm.resilient import ResilientClient

resilient = ResilientClient([("primary", client)], max_attempts=3, sleep=lambda _: None)
try:
    resilient.complete(LLMRequest(messages=question, model_alias="murshid-flagship",
                                  max_tokens=60))
except Exception as exc:
    print(type(exc).__name__, "-> every hop exhausted while the fault is on")

print(fault({"mode": "off"}), "\\n")
reply = resilient.complete(LLMRequest(messages=question, model_alias="murshid-flagship",
                                      max_tokens=60))
print("fault cleared, same client:", reply.model_id, "|", reply.text.strip()[:70])
'''),

    md("""
## 4. Serving open-weight models

The `vllm` route is an OpenAI-compatible server the application talks to with the
same adapter — the only difference above the boundary is which route name it asks
for, and that its residency is `on_premise`.
"""),
    code('''
for name in ("primary", "vllm"):
    route = settings.route(name)
    print(f"{name:<9} dialect={route.dialect:<8} residency={route.residency:<12} "
          f"model={route.resolve('murshid-flagship')}")

onprem = build_client(settings, "vllm")
reply = onprem.complete(LLMRequest(messages=question, model_alias="murshid-flagship",
                                   max_tokens=120))
print()
print("answered by:", reply.model_id, "| route:", reply.route)
print(reply.text.strip().splitlines()[1][:88])
'''),

    md("""
No code above the boundary changed — the route name did. That is the claim the
capstone rubric scores, and the reason it is worth the adapter: an on-premise
option stays open, and data residency becomes a configuration decision instead of
a rewrite.
"""),

    md("""
## 5. Commercial versus open-weight, decided like an engineer

Not "which is better" — *which one, for which slice of traffic, at what cost and
what latency*. The cost meter turns that into a table you can defend.
"""),
    code('''
from murshid.observability.cost import CostMeter

meter = CostMeter(settings.prices)
rows = []
for name in ("primary", "cheap", "comparison", "vllm"):
    c = build_client(settings, name)
    started = time.perf_counter()
    r = c.complete(LLMRequest(messages=question, model_alias="murshid-flagship", max_tokens=120))
    ms = (time.perf_counter() - started) * 1000
    record = meter.meter(r, route=name, intent="faq")
    rows.append((name, r.model_id, ms, r.usage.input_tokens, r.usage.output_tokens,
                 record.cost_halalas))

print(f"{'route':<11}{'model':<18}{'ms':>7}{'in':>6}{'out':>6}{'halalas':>10}")
for name, model, ms, tin, tout, cost in rows:
    print(f"{name:<11}{model:<18}{ms:>7.0f}{tin:>6}{tout:>6}{cost:>10.4f}")

cheapest = min(rows, key=lambda r: r[5])
dearest = max(rows, key=lambda r: r[5])
print()
print(f"{dearest[0]} costs {dearest[5] / cheapest[5]:.0f}x {cheapest[0]} on this one question")
'''),

    md("""
One question is not a benchmark. What makes this a decision rather than an anecdote
is running it over a corpus, at realistic concurrency, and reporting p50 **and**
p95 — a mean latency hides exactly the tail your users complain about.

The caveat that has to travel with every number here: this is the course gateway,
answering from rules. The **shape** of the comparison is real; the magnitudes are
this harness's, not any provider's.
"""),
    code('''
print("total metered this lab:", round(meter.total_halalas, 4), "halalas")
print("by route:", {k: round(v, 4) for k, v in meter.by("route").items()})
'''),

    md("""
## 6. Common mistakes

- **Assuming `temperature=0` means reproducible.** It does not; structure gives you
  stability, sampling parameters do not.
- **Counting tokens with one tokenizer for every route.** The Arabic premium above
  is the counter-example, and it changes the bill.
- **Retrying everything, or nothing.** The taxonomy is the point: retry 429 and
  5xx with backoff and jitter, fail fast on 400 and 401.
- **Comparing providers on one question.** A corpus, at concurrency, with p50 and
  p95 — otherwise it is a demo.
- **Treating open-weight as free.** It is a different cost shape — GPUs you rent by
  the hour rather than tokens you buy — and Module 6 works out the break-even.
"""),

    md("""
## Your turn — on your own project

The same two backends, on your own application:

1. **Two live routes, switchable by config** — one commercial, one open-weight. The
   claim the rubric scores is that swapping them is an environment variable, so
   prove it the way Lab 1's contract suite does: one test class, every adapter.
2. **Map the error taxonomy once**, in your adapter, into a single retryable flag.
   Anything unrecognised is not retryable.
3. **Run your own fault drill** and keep the log excerpt. A fallback chain that has
   never been exercised scores nothing.
4. **Start your `BENCHMARKS.md`** with a provider table you produced: p50 and p95,
   cost per call, and token counts under each route's own tokenizer.

**Next:** [Module 3 — structured outputs and tools](../modules/m3-structured-outputs-and-tools.qmd),
then [Lab 3](lab3-tickets-and-tools.ipynb).
"""),
]

if __name__ == "__main__":
    print("wrote", build("lab2-two-providers", "Lab 2 — two dialects behind one interface",
                         "Day 1 · after Module 2", LEAD, CELLS))

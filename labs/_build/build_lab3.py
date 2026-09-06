"""Lab 3 — Module 3's points, each demonstrated in code.

One section per numbered section of `modules/m3-structured-outputs-and-tools.qmd`:
the structured-output ladder, the repair loop measured on a real corpus, the
mechanics of function calling, tools designed to be used safely, and the negative
tests that are the actual deliverable.
"""

from __future__ import annotations

from nbbuild import SETUP, build, code, md

LEAD = """
Module 3 covered the structured-output ladder, the validate → retry → repair loop,
and a bounded tool loop whose authority lives outside the token stream. Each of
those is below, running against **Murshid** — including the failures, because the
failures are where the design shows.
"""

CELLS = [
    md("""
## Setup
"""),
    code(SETUP),

    md("""
## 1. The structured-output ladder

Four rungs: prompt-and-pray, JSON mode, **strict schema**, and function calling.
Climb to the highest rung the route supports, and validate anyway.

Murshid's contract is a Pydantic model, and the strict-mode JSON Schema is
generated from it — one definition, not two that drift.
"""),
    code('''
import json

from murshid.domain.ticket import ServiceTicket, schema_violations, strict_schema

print("fields:", ", ".join(ServiceTicket.model_fields))
schema = strict_schema()
print("envelope:", list(schema), "->", list(schema["json_schema"]))
print("strict:", schema["json_schema"]["strict"])
'''),

    md("""
Strict mode is a **narrower subset** than JSON Schema: every property required,
`additionalProperties: false` everywhere, and a short list of unsupported keywords.
A schema that validates as JSON Schema can still be rejected by the API, so the
repository has a check that runs in CI rather than a comment saying "be careful".
"""),
    code('''
print("violations in Murshid's contract:", schema_violations(schema) or "none")

# The classic trap: making a field optional. Strict mode has no optional
# properties — everything is required, and "may be absent" is expressed as a
# nullable type instead.
bad = json.loads(json.dumps(schema))
bad["json_schema"]["schema"]["required"].remove("urgency")
for problem in schema_violations(bad):
    print("violation:", problem)
'''),

    md("""
The schema carries the shape. It cannot carry the *rules* — a Saudi national ID is
ten digits starting 1 or 2, and no `type: string` expresses that. Validators do,
and they run on every parse.
"""),
    code('''
from pydantic import ValidationError

from murshid.domain.ticket import Applicant
from murshid.pipeline.structured import render_errors

for candidate in ({"full_name": "Sara Al-Otaibi", "national_id": "1055555555"},
                  {"full_name": "Sara Al-Otaibi", "national_id": "12345"},
                  {"full_name": "Sara Al-Otaibi", "national_id": "9055555555"}):
    try:
        applicant = Applicant(**candidate)
        print("accepted:", applicant.national_id)
    except ValidationError as exc:
        print("rejected:", candidate["national_id"], "->", render_errors(exc).strip())
'''),

    md("""
One field deserves its own paragraph: `national_id` is `str | None`. **`None` means
the citizen did not give one**, and that is a different fact from a plausible ten
digits the model produced to fill the slot. An invented identifier is the most
expensive kind of wrong, because everything downstream trusts it.
"""),
    code('''
print(Applicant(full_name="Sara Al-Otaibi").model_dump())
'''),

    md("""
## 2. The validate → retry → repair loop

Extraction is not "call the model and parse". It is: call, validate, and on failure
send the **validation errors back** as the next turn's input. Second failure
escalates — a third attempt is a loop, not a strategy.

Watch it repair. The scripted client returns an invalid `urgency` first, then a
valid one, so the loop's control flow is visible rather than inferred.
"""),
    code('''
from murshid.llm.fake import FakeClient
from murshid.pipeline.extract import extract_ticket

wobbly = FakeClient(model_id="wobbly")
wobbly.script_json({"service_type": "commercial_licence", "summary_en": "renew a CR",
                    "city": "Riyadh", "urgency": "soon",          # not in the enum
                    "language": "en", "applicant": {"full_name": "Sara Al-Otaibi"},
                    "needs_human": False})
wobbly.script_json({"service_type": "commercial_licence", "summary_en": "renew a CR",
                    "city": "Riyadh", "urgency": "urgent",        # repaired
                    "language": "en", "applicant": {"full_name": "Sara Al-Otaibi"},
                    "needs_human": False})

ticket, outcome = extract_ticket(wobbly, "I need to renew my licence, it is urgent")
print("attempts:", outcome.attempts, "| first try:", outcome.first_try,
      "| urgency:", ticket.urgency)
print()
print("what the second turn was told:")
print(wobbly.requests[-1].messages[-1].content.strip()[:220])
'''),

    md("""
The repair prompt is the validator's own error text. No cleverness — the model is
told exactly which field failed and why, which is why one retry usually suffices.

Now the same loop against a live route, over a real corpus, because a rate is the
only honest way to report this. `CorpusReport` splits by language, since Arabic and
English do not fail at the same rate and an average hides that.
"""),
    code('''
import json

from murshid.app import build_client
from murshid.config import get_settings
from murshid.pipeline.extract import CorpusReport, ExtractionFailed

settings = get_settings()
client = build_client(settings, settings.primary_route)

def jsonl(name):
    with open(f"data/{name}", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]

corpus = jsonl("citizen_messages_50.jsonl")
# 15 of those cases are annotated with the fields the message does NOT contain, so
# a ticket that fills one in has invented it.
audit = {row["id"]: row["absent_fields"] for row in jsonl("extract_audit_15.jsonl")}

report = CorpusReport()

# Fifty extractions, each logging its own validation failures. The rate is the
# lesson here, not the individual failures, so the log is muted for the loop.
with quiet():
    for row in corpus:
        language = row["gold"]["language"]
        try:
            ticket, outcome = extract_ticket(client, row["text"])
        except ExtractionFailed:
            # Two validation failures in a row is a hand-off, not a third attempt.
            report.record(language, "escalated")
            continue
        report.record(language, "first_try" if outcome.first_try else "after_repair")

        for field in audit.get(row["id"], []):
            if field == "applicant.national_id" and ticket.applicant.national_id:
                report.invented_fields += 1
            if field == "city" and ticket.city != "unknown":
                report.invented_fields += 1

print(report.render())
print(f"   invented fields across {len(audit)} annotated cases: {report.invented_fields}")
'''),

    md("""
Read the slices, not the headline. If one language repairs far more often than the
other, that is a prompt problem in one language — and the average would have hidden
it. `invented_fields` is the audit: fifteen of those cases are annotated with the
fields their message does *not* contain, so a ticket that fills one in has made it
up. That is the number that has to be zero.
"""),

    md("""
## 3. Function calling: the mechanics

A tool call is not the model running code. It is the model **emitting a request**,
your application deciding whether to honour it, running the function, and feeding
the result back as a `tool` message. Four steps, and the application owns three.
"""),
    code('''
from murshid.tools.registry import tool_schemas

for schema in tool_schemas():
    fn = schema["function"]
    print(f"{fn['name']:<26} args={list(fn['parameters'].get('properties', {}))}")
'''),

    code('''
from murshid.domain.session import Session
from murshid.llm.interfaces import Message
from murshid.pipeline.tool_loop import run_with_tools

session = Session(citizen_id="citizen-A")
scripted = FakeClient(model_id="tooly")
scripted.script_tool_call("check_application_status", {"reference": "CR12345678"})
scripted.script_text("Your application is with the review team; it was updated yesterday.")

result = run_with_tools(scripted, [Message(role="user", content="Where is CR12345678?")],
                        session, allowed_tools=["check_application_status"])

print("iterations:", result.iterations)
print("tool calls :", [c["tool"] for c in result.calls])
print("final text :", result.text)
'''),

    md("""
Two iterations: one to ask for the tool, one to answer with its result. What the
model saw on the second turn is the `tool` message — plain data your application
put there.
"""),
    code('''
for message in scripted.requests[-1].messages:
    print(f"{message.role:<10} {str(message.content)[:88]}")
'''),

    md("""
## 4. Designing tools the model uses well — and safely

Three risk classes, and the class decides the treatment: read-only runs freely,
side-effecting passes a gate and is idempotent, terminal ends the turn.

Notice what is **not** in `book_appointment`'s schema: any way to say who the
booking is for. Identity comes from the session. The model cannot ask for someone
else's appointment because there is no field in which to ask.
"""),
    code('''
print("book_appointment parameters:",
      list(tool_schemas(["book_appointment"])[0]["function"]["parameters"]["properties"]))
print()
print("the model tries anyway:")
print(session.authorize("book_appointment", {"citizen_id": "citizen-B"}))
'''),

    md("""
That is defence in depth: the schema does not offer the field, and the gate refuses
it if it arrives anyway — because a tool argument is user input by proxy, and an
injected instruction can reach it. The same gate holds when identity has gone
stale.
"""),
    code('''
stale = Session(citizen_id="citizen-A", identity_verified=False)
verdict = stale.authorize("book_appointment", {"service_type": "commercial_licence"})
print("allowed:", verdict.allowed, "| reason:", verdict.reason)
print("what the citizen is told:", verdict.user_hint)
'''),

    md("""
Descriptions are part of the interface. A tool the model uses at the wrong moment
is usually a description problem, not a model problem — say when to use it, when
**not** to, and what it returns.
"""),
    code('''
print(tool_schemas(["check_application_status"])[0]["function"]["description"])
'''),

    md("""
## 5. The negative tests are the deliverable

The happy path proves nothing. These four are what a reviewer looks for.

**A hallucinated tool name.** The loop refuses it and tells the model, rather than
crashing.
"""),
    code('''
ghost = FakeClient(model_id="tooly")
ghost.script_tool_call("delete_all_records", {})
ghost.script_text("I don't have a tool that can do that.")

out = run_with_tools(ghost, [Message(role="user", content="delete everything")],
                     Session(), allowed_tools=["check_application_status"])
print("tools actually run:", out.calls)
print("answer:", out.text)
'''),

    md("""
**A loop that never ends.** The bound is a number, not a hope, and hitting it hands
off to a human.
"""),
    code('''
endless = FakeClient(model_id="tooly").script_endless_tool_calls(
    "check_application_status", {"reference": "CR12345678"})

out = run_with_tools(endless, [Message(role="user", content="status?")], Session(),
                     allowed_tools=["check_application_status"], max_iterations=4)
print("bound hit:", out.bound_hit, "| iterations:", out.iterations)
print("answer:", out.text)
'''),

    md("""
**Malformed arguments.** A date outside the booking window is a domain rule the
schema cannot express, so a validator holds it — and the error goes back to the
model as data.
"""),
    code('''
import datetime as dt

from murshid.domain.ticket import BookingRequest

for offset, label in ((14, "two weeks out"), (400, "next year")):
    date = dt.date.today() + dt.timedelta(days=offset)
    try:
        BookingRequest(service_type="commercial_licence", city="Jeddah", date=date)
        print(f"{label:<14} {date} accepted")
    except ValidationError as exc:
        print(f"{label:<14} {date} rejected ->", render_errors(exc).strip())
'''),

    md("""
**A retried turn that must not act twice.** The idempotency key is derived from the
tool name and its arguments, so the same booking replayed returns the first result
instead of making a second appointment.
"""),
    code('''
booking_args = {"service_type": "commercial_licence", "city": "Jeddah",
                "date": (dt.date.today() + dt.timedelta(days=14)).isoformat()}
citizen = Session(citizen_id="citizen-A")

for attempt in (1, 2):
    client_ = FakeClient(model_id="tooly")
    client_.script_tool_call("book_appointment", booking_args)
    client_.script_text("Your appointment is booked.")
    run_with_tools(client_, [Message(role="user", content="book it")], citizen,
                   allowed_tools=["book_appointment"])
    print(f"attempt {attempt}: side effects recorded = {len(citizen.completed_side_effects)}")

print()
print("one key, so the second turn replayed instead of booking again:")
print(list(citizen.completed_side_effects)[0][:60], "...")
'''),

    md("""
## 6. Common mistakes

- **Parsing without validating.** JSON that loads is not a ticket that is correct.
- **Retrying with the same prompt.** The repair turn must carry the errors, or it
  is the same call with a different random seed.
- **Putting identity in the tool arguments.** The token stream is not a trust
  boundary; the session is.
- **Reporting the happy path.** The four negative tests above are the deliverable —
  a submission with none of them scores on this criterion no matter how well the
  demo goes.
- **A schema that is valid JSON Schema but not valid strict mode.** Check it in CI.
"""),

    md("""
## Your turn — on your own project

Your domain has a request object and a set of actions. Build them:

1. **One validated contract** — a ticket, an enrolment, a return — with validators
   carrying the rules the schema cannot express, and a `None` that means "not
   given" rather than an invented value.
2. **The repair loop, measured.** Run your own messy corpus through it and report
   first-try and after-repair rates split by language. A corpus where nothing ever
   escalates is not testing the failure path.
3. **Three tools across the risk classes** — read-only, side-effecting, terminal —
   with the side-effecting one behind a gate that reads the authenticated session
   and never the model's arguments.
4. **Your own negative tests**: acting for someone else, a hallucinated tool name,
   malformed arguments, and a retried turn that must not act twice.

**Next:** [Module 4 — prompts and guardrails](../modules/m4-prompts-and-guardrails.qmd),
then [Lab 4](lab4-guarded-pipeline.ipynb).
"""),
]

if __name__ == "__main__":
    print("wrote", build("lab3-tickets-and-tools", "Lab 3 — structured output, and tools that act",
                         "Day 2 · after Module 3", LEAD, CELLS))

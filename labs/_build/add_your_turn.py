"""Append a "Your turn" cell to each lab, on the reader's own capstone project.

Murshid is the worked example the labs run on; the capstone is the reader's own
application. Every lab now ends by naming the same points, applied to their track
— which is how the building-agents assignments are written ("do X, as in the
lesson", on your own build).

Markdown-only, appended to the executed notebooks in place, so the outputs stay
exactly as the container produced them.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

LABS = Path(r"C:\Users\fdasg\Projects\SDAIA-Training\llm-application-engineering\labs")

TURNS: dict[str, str] = {
    "lab1-skeleton": """
## Your turn — on your own project

Everything above ran against Murshid, the worked example. The capstone is **your**
application, on the track you pick, and it needs the same four things from this
module. Start them now rather than on Day 4:

1. **Name the shape.** Which of the four patterns does your traffic want — a single
   call, a workflow, a router, or a bounded agentic loop? Write one paragraph
   justifying it against the traffic mix you expect. That paragraph is the first
   ADR the rubric asks for.
2. **Draw the boundary before you write an adapter.** One interface your
   application talks to, with a normalised request and response that carry
   `model_id`, `usage` and a finish reason. Copy the shape from
   `src/murshid/llm/interfaces.py` if you like — that is what a reference
   implementation is for.
3. **Decide your state strategy** and say what it costs. Windowed is the safe
   default; if you pick summarisation, you owe the eval cases that show a long
   conversation still remembers what matters.
4. **Write your own context budget.** Your directory, your tool schemas, your
   history. Measure the numbers rather than guessing them.

Then run this notebook's commands against your own project as it grows.
""",
    "lab2-two-providers": """
## Your turn — on your own project

The same two backends, on your own application:

1. **Two live routes, switchable by config** — one commercial, one open-weight.
   The claim the rubric scores is that swapping them is an environment variable,
   so prove it the way the contract suite above does: one test class, every
   adapter.
2. **Map the error taxonomy once**, in your adapter, into a single retryable
   flag. Anything unrecognised is not retryable.
3. **Run your own fault drill** and keep the log excerpt. A fallback chain that
   has never been exercised scores nothing.
4. **Start your `BENCHMARKS.md`** with a provider table you produced: p50 and p95,
   cost per call, and the token counts under each route's own tokenizer.
""",
    "lab3-tickets-and-tools": """
## Your turn — on your own project

Your domain has a request object and a set of actions. Build them:

1. **One validated contract** — a ticket, an enrolment, a return — with validators
   carrying the rules the schema cannot express, and a `None` that means "not
   given" rather than an invented value.
2. **The repair loop, measured.** Run your own messy corpus through it and report
   first-try and after-repair pass rates, split by language. Escalation on the
   second failure is a feature; a corpus where nothing escalates is not testing
   the failure path.
3. **Three tools across the risk classes** — read-only, side-effecting, terminal —
   with the side-effecting one behind a gate that reads the authenticated session
   and never the model's arguments.
4. **Your own negative tests.** Booking for someone else, a hallucinated tool
   name, malformed arguments, a retried turn that must not act twice. Those tests
   are the deliverable, not the happy path.
""",
    "lab4-guarded-pipeline": """
## Your turn — on your own project

Guards are the section most often lost on a number reported alone. On your app:

1. **Every prompt a versioned file** with front matter and a changelog, no prompt
   text in code, and the served version in your request log.
2. **A pipeline of named stages**, each runnable alone in a test against stubs.
3. **Your own two corpora** — attacks in both languages, and a legitimate corpus
   with deliberate traps that a naive pattern would block. Report the block rate
   **and** the false-positive rate, always together, from the same command.
4. **A canary and an outbound wall.** The pass condition is that your system
   prompt does not leak, not that everything is blocked.
5. **Designed refusals**, bilingual, that never echo the payload.
""",
    "lab5-evaluation-harness": """
## Your turn — on your own project

This is the heaviest section in the rubric, and the one that cannot be produced on
Day 4:

1. **A golden set of at least 120 cases**, stratified by intent, language,
   difficulty and risk, with safety oversampled and every expectation approved by
   someone who owns the facts. Build it as you go; it is not a Day 4 task.
2. **A harness that runs your real pipeline**, not a simplified copy, and reports
   slices rather than one number.
3. **Deterministic asserts for every safety claim.** A judge may track quality,
   but only after you have calibrated it against human labels and can show κ.
4. **A gate that has actually blocked something.** Seed a regression into your own
   prompt, watch the slice table catch it, and keep that output.
5. **`EVALUATION_REPORT.md` with a known-limitations section.** A report with no
   limitations is a report nobody believes.
""",
    "lab6-optimise": """
## Your turn — on your own project

Same order, on your own traffic — and the order is the lesson:

1. **Meter before you optimise.** Aggregate your own cost log and say out loud
   where the money goes. Optimising before measuring is how a week goes into the
   4% line item.
2. **Prefix discipline**, proven by cached-token counts rather than asserted.
3. **A response cache whose key carries everything that changes an answer**, and a
   semantic tier only if you also build the near-miss suite that keeps it honest.
   Zero wrong hits is the bar.
4. **A routing table, eval-gated.** If it fails the gate, read which slice failed
   before you hand the saving back — a cascade with a deterministic escalation
   signal may buy the points back for nothing.
5. **A break-even from throughput you measured**, quoting both comparisons, in
   your ADR.

Every row of your before/after table carries its eval verdict. A row without one
does not count.
""",
}

for slug, markdown in TURNS.items():
    path = LABS / f"{slug}.ipynb"
    nb = nbformat.read(path, as_version=4)
    if any("Your turn — on your own project" in c.source for c in nb.cells):
        print(f"{slug}: already present, skipped")
        continue
    nb.cells.append(nbformat.v4.new_markdown_cell(markdown.strip("\n")))
    nbformat.write(nb, path)
    outputs = sum(1 for c in nb.cells if c.get("outputs"))
    print(f"{slug}: appended ({outputs} output cells still intact)")

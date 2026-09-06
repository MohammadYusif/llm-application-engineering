"""Reshape each lab from a timed task sheet into one explanation of its module.

The lab is now a single file that walks the points its module explained, in the
module's own order and vocabulary, running each one against Murshid — and closes
by handing the same points to the reader for their own capstone.

What goes: the objective block, the "1 · … (10 min)" numbering, the troubleshooting
tables (the site has a Troubleshooting page), the commit chores and the
finish-early extras. What stays: the explanation, the code, the outputs, and the
your-turn close.

Markdown only, applied to the executed notebooks in place, so the outputs stay
exactly as the container produced them.
"""

from __future__ import annotations

import re
from pathlib import Path

import nbformat

LABS = Path(r"C:\Users\fdasg\Projects\SDAIA-Training\llm-application-engineering\labs")

LEAD = {
    "lab1-skeleton": (
        "Lab 1 — the model boundary, in code",
        "Module 1 argued for one boundary between the application and the provider, "
        "a pattern chosen on evidence, windowed state, and reliability policy in a "
        "single place. This notebook runs each of those against **Murshid**, the "
        "worked example, so you can see what each one looks like before you build "
        "your own.",
    ),
    "lab2-two-providers": (
        "Lab 2 — two dialects behind one interface",
        "Module 2 covered the two wire dialects, tokens counted per route, the error "
        "taxonomy, and an open-weight model served behind the same interface. Here "
        "is each of those running against Murshid.",
    ),
    "lab3-tickets-and-tools": (
        "Lab 3 — structured output, and tools that act",
        "Module 3 covered the structured-output ladder, the validate → retry → repair "
        "loop, and a bounded tool loop whose authorisation lives outside the token "
        "stream. Here is each of those running against Murshid.",
    ),
    "lab4-guarded-pipeline": (
        "Lab 4 — the prompt pipeline and its walls",
        "Module 4 covered prompts as versioned artefacts, a pipeline of stages that "
        "can each be tested alone, a layered input wall and an outbound wall. Here is "
        "each of those running against Murshid — including the two attacks that are "
        "supposed to get through.",
    ),
    "lab5-evaluation-harness": (
        "Lab 5 — the harness, the judge, and the gate",
        "Module 5 covered golden sets that earn their authority from construction, a "
        "metric for every claim, judges you qualify before you trust, and a gate that "
        "reads slices. Here is each of those running against Murshid.",
    ),
    "lab6-optimise": (
        "Lab 6 — cost and latency, measured first",
        "Module 6 covered metering before optimising, prompt-cache discipline, "
        "response caching with a near-miss suite, and routing with a cascade — every "
        "step eval-gated. Here is each of those running against Murshid.",
    ),
}

# Old heading -> the module's own vocabulary for the same point.
RENAME = {
    "0 · Five minutes with a demo that works on stage": "How LLM applications fail quietly",
    "1 · The skeleton (10 min)": "The layered skeleton, and the test that enforces it",
    "2 · The boundary (15 min)": "The model boundary",
    "3 · Windowed state and the CLI (10 min)": "Windowed state",
    "4 · The context budget (10 min)": "The context budget",
    "5 · Reliability, under a real fault": "Reliability, under a real fault",

    "1 · The contract suite (12 min)": "One contract suite, every adapter",
    "2 · The open-weight route, with no code change (8 min)": "The open-weight route, with no code change",
    "3 · Streaming and time-to-first-token (12 min)": "Streaming, and time-to-first-token",
    "4 · The fault drill (10 min)": "The error taxonomy, under a real 429",
    "5 · The bench table (8 min)": "The bench table",

    "1 · The contract (10 min)": "The contract, and what a schema cannot express",
    "2 · The repair loop (15 min)": "The validate → retry → repair loop",
    "3 · Measure the corpus (15 min)": "Schema-pass rate, split by language",
    "4 · The comparison (10 min)": "The same corpus on another route",
    "5 · Tool descriptions route (10 min)": "Tool descriptions route",
    "6 · Bounds and the authorisation gate (15 min)": "Bounds, and the authorisation gate",
    "7 · End to end (15 min)": "End to end",

    "1 · Prompts into the registry (8 min)": "Prompts as versioned artefacts",
    "2 · Assemble the pipeline (12 min)": "The pipeline, stage by stage",
    "3 · The guards, and both numbers (15 min)": "Input guards, and both numbers",
    "4 · The canary (8 min)": "The canary",
    "5 · The trade-off, as a product decision (7 min)": "The false positives that matter",
    "6 · The indirect vector": "The indirect vector",
    "7 · Record the misses — do not fix them": "The two misses, recorded",

    "1 · Absorb the corpora (8 min)": "The golden set, and its strata",
    "2 · Run it, and read the slices (10 min)": "The harness, and why the average lies",
    "3 · Calibrate the judge (12 min) — the centrepiece": "Calibrating the judge",
    "4 · Wire the gate, then break it (8 min)": "The gate, and breaking it on purpose",
    "5 · The report (4 min)": "The report",

    "1 · Meter first, and name where the money goes (8 min)": "Meter first",
    "2 · Prompt-cache discipline (10 min)": "Prompt-cache discipline",
    "3 · The response cache, and its safety suite (12 min)": "Response caching, and its safety suite",
    "4 · The routing table, and the correction (12 min)": "Routing, and the correction",
    "5 · The break-even, and the ADR (5 min)": "The break-even",
    "6 · The leaderboard (3 min)": "The leaderboard",
}

# Sections that are chores or overflow rather than part of the module's argument.
DROP_SECTIONS = ("## Troubleshooting", "## If you finish early", "## 6 · Commit",
                 "## 8 · Commit", "# Part A — the ticket", "# Part B — the tool loop")


def strip_dropped(src: str) -> str:
    """Remove a dropped section and everything under it, up to the next heading."""
    out, skipping = [], False
    for line in src.split("\n"):
        if any(line.strip().startswith(d) for d in DROP_SECTIONS):
            skipping = True
            continue
        if skipping:
            if re.match(r"^#{1,3} ", line) and not any(
                line.strip().startswith(d) for d in DROP_SECTIONS
            ):
                skipping = False
            else:
                continue
        out.append(line)
    return "\n".join(out)


for slug, (title, lead) in LEAD.items():
    path = LABS / f"{slug}.ipynb"
    nb = nbformat.read(path, as_version=4)

    # 1. Title cell + lead, replacing the objective block that followed it.
    subtitle = nb.cells[0].source.split("*")[1] if "*" in nb.cells[0].source else ""
    nb.cells[0].source = f"# {title}\n\n*{subtitle}*\n\n{lead}"
    if nb.cells[1].cell_type == "markdown" and "callout-note" in nb.cells[1].source:
        nb.cells.pop(1)

    # 2. Headings into the module's vocabulary; 3. chores and overflow out.
    kept = []
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            kept.append(cell)
            continue
        src = cell.source
        for old, new in RENAME.items():
            src = src.replace(f"## {old}", f"## {new}")
        src = strip_dropped(src)
        if src.strip():
            cell.source = src.strip("\n")
            kept.append(cell)
    nb.cells = kept

    nbformat.write(nb, path)
    heads = [l for c in nb.cells if c.cell_type == "markdown"
             for l in c.source.split("\n") if l.startswith("## ")]
    outs = sum(1 for c in nb.cells if c.get("outputs"))
    print(f"{slug}: {len(nb.cells)} cells, {outs} with output")
    for h in heads:
        print(f"    {h}")

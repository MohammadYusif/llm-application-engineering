"""Generate `Capstone Rubric - Large Language Model Application Engineering.pdf`.

    python course/make_rubric_pdf.py [output-directory]

SDAIA Academy requires one rubric PDF per course, carrying that course's rubric
plus the standing GitHub and documentation requirements that apply to every
project in every programme. The layout follows the existing course rubrics so a
trainee who has seen one recognises the next.

The rubric text here and `grader/grading/rubrics/llm-application-engineering.yaml`
are the same rubric in two forms: this one is what a participant reads, that one
is what the engine can check. When they disagree, this file is the requirement
and the YAML is an approximation of it - the engine cannot see a measured pass
rate, a false-positive pair, or a live demo, and says so in its own header.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TITLE = "Large Language Model Application Engineering"
FILENAME = f"Capstone Rubric - {TITLE}.pdf"

INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5A5A5A")
RULE = colors.HexColor("#C9C9C9")
BAND = colors.HexColor("#EEEAF1")
ACCENT = colors.HexColor("#4A3A52")

styles = getSampleStyleSheet()
H1 = ParagraphStyle(
    "H1", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=21,
    alignment=TA_LEFT, textColor=INK, spaceAfter=2,
)
H2 = ParagraphStyle(
    "H2", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12.5, leading=16,
    textColor=ACCENT, spaceBefore=14, spaceAfter=6,
)
H3 = ParagraphStyle(
    "H3", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14,
    textColor=INK, spaceBefore=10, spaceAfter=4,
)
SUB = ParagraphStyle(
    "SUB", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11.5, leading=15,
    textColor=MUTED, spaceAfter=2,
)
META = ParagraphStyle(
    "META", parent=styles["Normal"], fontName="Helvetica", fontSize=8.6, leading=12,
    textColor=MUTED, spaceAfter=10,
)
BODY = ParagraphStyle(
    "BODY", parent=styles["Normal"], fontName="Helvetica", fontSize=9.2, leading=13,
    textColor=INK, spaceAfter=6,
)
CELL = ParagraphStyle(
    "CELL", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, leading=11.4,
    textColor=INK,
)
CELL_B = ParagraphStyle("CELL_B", parent=CELL, fontName="Helvetica-Bold")
CELL_H = ParagraphStyle("CELL_H", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
NOTE = ParagraphStyle(
    "NOTE", parent=BODY, fontSize=8.6, leading=12, textColor=MUTED, spaceBefore=4,
)

DELIVERABLES: list[tuple[str, str, str, str]] = [
    (
        "1",
        "Architecture &amp; the Model Boundary",
        "15",
        "A router-first design: an FAQ single-call path, a service workflow with tools, and an "
        "escalation path to a human. <b>Every</b> model call goes through one internal client "
        "interface; no application module imports a provider SDK. Two live backends, one "
        "commercial API and one open-weight, switchable by configuration rather than by code. "
        "Reliability policy at that boundary and demonstrated under a fault: timeouts always, "
        "capped retries with backoff that honours Retry-After, a fallback chain ending in a "
        "degraded but honest answer. One ADR recording the pattern and the model choices.",
    ),
    (
        "2",
        "Structured Outputs &amp; Function Calling",
        "15",
        "One validated request object for your domain: schema-constrained generation over the "
        "wire, a pydantic "
        "contract whose validators carry the semantics the schema cannot express, and a "
        "validate &#8594; retry &#8594; repair loop that feeds the located validation errors back "
        "once and then escalates by design. Schema-pass rates measured and reported, split by "
        "language. A bounded tool loop over at least three tools spanning the risk classes, with an "
        "authorisation gate that reads the authenticated session and never the model's own "
        "arguments. The negative tool-safety tests all pass, and every tool call is logged with "
        "its risk class and loop iteration.",
    ),
    (
        "3",
        "Prompt Pipeline &amp; Guardrails",
        "15",
        "All prompts are versioned artefacts in a registry with front-matter and a changelog; "
        "zero prompt text inline in code, enforced in CI; the served prompt version appears in "
        "the request log. A five-stage pipeline whose every stage is testable alone. A layered "
        "input wall (deterministic patterns in <b>both</b> languages, Saudi PII masking before "
        "any model or log sees the text, then a cheap-model classifier) and an outbound wall "
        "(canary leak check, outbound PII, relayed instructions). Attack corpus &#8805; 95% "
        "blocked <b>with</b> 0% false positives on the legitimate corpus. Refusals are designed, "
        "bilingual, and never echo the payload.",
    ),
    (
        "4",
        "Evaluation Harness",
        "20",
        "A golden set of at least 120 cases, stratified by intent, language, difficulty and risk "
        "class, Arabic-majority, with safety cases oversampled and every expectation owner-"
        "approved. A harness that runs the set through the <b>real</b> pipeline, not a simplified "
        "copy. Deterministic asserts carry every safety claim; a judge contributes tracking "
        "signal only and is calibrated against human labels to Cohen's &#954; &#8805; 0.6, with "
        "the calibration evidence included. The safety stratum at 100%. A CI regression gate that "
        "reads slices rather than the average, demonstrated blocking a seeded change. "
        "EVALUATION_REPORT.md generated from real runs, including known limitations.",
    ),
    (
        "5",
        "Cost &amp; Latency Engineering",
        "15",
        "A cost meter covering 100% of model calls, guards and router included, aggregating by "
        "route and intent. Prompt-cache discipline proven by the usage fields rather than "
        "asserted: a byte-stable prefix, a volatile tail, and cached-token counts to show it. A "
        "response cache whose key carries everything that changes an answer, with a semantic "
        "tier that is scoped, thresholded on measured data, and evaluated against a near-miss "
        "suite at zero wrong hits. A documented before/after in BENCHMARKS.md reaching "
        "&#8805; 60% cost reduction per conversation, with the eval verdict recorded beside "
        "every step.",
    ),
    (
        "6",
        "Model Comparison &amp; Recommendation",
        "10",
        "The commercial and open-weight backends both run over <b>your own</b> golden set, "
        "reported by slice rather than as one number, with cost and latency alongside quality. "
        "A self-host break-even computed from throughput you measured, not from a vendor "
        "figure, and a routing recommendation that follows from both. Recorded in the ADR, with "
        "the evidence attached, so that reopening the question later is a re-run rather than a "
        "re-argument.",
    ),
    (
        "7",
        "The Application, Complete",
        "10",
        "A stranger can clone the repository and reach a working bilingual conversation in ten "
        "minutes by following the README. A single-command entry point rather than a list of "
        "steps. A five-minute live demo exercising four things: an FAQ answer, a "
        "tool-completed booking, a refused attack, and a graceful fallback; then one adversarial "
        "question from the floor, answered by the running system.",
    ),
]

EVALUATION_NOTES = [
    "<b>Grade from the artefacts first, the demo second.</b> CI history, EVALUATION_REPORT.md, "
    "the meter logs and the corpus numbers are the evidence; the course's thesis is that the "
    "repository proves the system.",
    "<b>Presence is not effect.</b> A library imported but never called, a guard that nothing "
    "runs, a gate that cannot fail, or a golden case that asserts nothing does not satisfy a "
    "deliverable.",
    "<b>A held-out set is run against every submission before the demos.</b> A large gap between "
    "your reported numbers and that run is the first discussion point, not an automatic penalty.",
    "<b>Four things cap a criterion at 70%:</b> golden cases edited to make failures pass; guard "
    "numbers reported without the false-positive pair; cost savings with no eval verdict beside "
    "them; a judge gating anything without calibration evidence.",
    "<b>Expect to be asked to break something live</b> and show which gate catches it: lower the "
    "semantic threshold, unpin a model, remove a guard layer.",
]

GITHUB_MANDATORY = [
    "Every trainee must create and activate a GitHub account if they do not already have one.",
    "All AI-related training projects must be uploaded to GitHub, kept documented and "
    "continuously updated.",
    "A project not published to GitHub as described here is not a complete submission.",
]

REPO_REQUIREMENTS: list[tuple[str, str]] = [
    (
        "Clear, comprehensive project description",
        "What the assistant does, the problem it solves, its architecture (router, guarded "
        "pipeline, model boundary, evaluation harness), and its scope &#8212; visible from the "
        "repository landing page.",
    ),
    (
        "Professional README",
        "Explains the project idea and how to run and use it: prerequisites, the environment "
        "variables each route needs, install and setup steps, how to run the tests and the "
        "harness, and the expected output.",
    ),
    (
        "Proper technical documentation",
        "The architecture and its layers, the prompt registry and its versions, the guard layers, "
        "the golden set's strata, and the ADRs behind the pattern and model choices.",
    ),
    (
        "Good Git version-control practices",
        "Meaningful commit messages, an incremental history through the labs rather than one bulk "
        "upload, a sensible repository structure, and a .gitignore that excludes secrets, API "
        "keys and generated files.",
    ),
    (
        "Training program attribution",
        "State clearly which training program the project was completed under: the program name "
        "and the cohort or session dates.",
    ),
    (
        "Link to SDAIA Academy on GitHub",
        "Reference https://github.com/SDAIAAcademy in the README where relevant.",
    ),
]

ENCOURAGED = [
    "Starring high-quality repositories.",
    "Following Saudi accounts and repositories.",
    "Contributing to open-source projects.",
    "Engaging through Fork, Pull Requests, and Issues where appropriate.",
    "Sharing standout projects with the wider tech community.",
]


def bullets(items: list[str], style: ParagraphStyle = BODY) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=10) for t in items],
        bulletType="bullet",
        bulletFontSize=6,
        bulletOffsetY=-1.5,
        leftIndent=12,
        spaceBefore=2,
        spaceAfter=6,
    )


def rubric_table() -> Table:
    data = [[
        Paragraph("#", CELL_H),
        Paragraph("Deliverable", CELL_H),
        Paragraph("Pts", CELL_H),
        Paragraph("What is required", CELL_H),
    ]]
    for number, name, points, text in DELIVERABLES:
        data.append([
            Paragraph(number, CELL_B),
            Paragraph(name, CELL_B),
            Paragraph(points, CELL_B),
            Paragraph(text, CELL),
        ])
    table = Table(data, colWidths=[8 * mm, 34 * mm, 9 * mm, 116 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


TRACKS: list[tuple[str, str, str]] = [
    ("A", "Citizen services",
     "Renewals, fees, documents and appointments for a fictional authority. The course's own "
     "reference shape: grounded FAQ, a booking that acts, an escalation path to a human."),
    ("B", "Campus services",
     "Admissions, enrolment, transcripts and advisor appointments. Facts that must be quoted "
     "exactly, a side-effecting booking, and a student-privacy problem to solve."),
    ("C", "Internal IT service desk",
     "Access requests, asset bookings, incident triage and hand-off to a human. Authorisation "
     "is the whole game: who is asking decides what may be done."),
    ("D", "Retail order support",
     "Order status, returns, exchanges and store appointments. Lookups are read-only, returns "
     "act, and the product catalogue is the grounding."),
]


def tracks_table() -> Table:
    data = [[
        Paragraph("Track", CELL_H),
        Paragraph("The application", CELL_H),
        Paragraph("Why it needs the whole course", CELL_H),
    ]]
    for letter, name, why in TRACKS:
        data.append([
            Paragraph(letter, CELL_B), Paragraph(name, CELL_B), Paragraph(why, CELL),
        ])
    table = Table(data, colWidths=[12 * mm, 36 * mm, 119 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def requirements_table() -> Table:
    data = [[Paragraph("Requirement", CELL_H), Paragraph("What it means in practice", CELL_H)]]
    for name, meaning in REPO_REQUIREMENTS:
        data.append([Paragraph(name, CELL_B), Paragraph(meaning, CELL)])
    table = Table(data, colWidths=[46 * mm, 121 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, f"{TITLE}  |  SDA-AIE-213  |  Capstone rubric")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 15.5 * mm, 190 * mm, 15.5 * mm)
    canvas.restoreState()


def build(out_dir: Path) -> Path:
    out = out_dir / FILENAME
    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"Capstone Rubric - {TITLE}",
        author="SDAIA Academy",
        subject="SDA-AIE-213 capstone rubric and submission requirements",
    )

    story: list = [
        Paragraph(TITLE, H1),
        Paragraph("Capstone Rubric &amp; Submission Requirements", SUB),
        Paragraph(
            "SDAIA Academy, delivered via Learning Space  |  4-day capstone  |  "
            "20 training hours  |  Course code SDA-AIE-213",
            META,
        ),
        Paragraph("1. Choose One Track", H2),
        Paragraph(
            "The capstone is <b>your own</b> application. Murshid, the bilingual "
            "citizen-services assistant used as the worked example throughout the course, is "
            "what you learn from &#8212; it is not what you submit, and a submission that is "
            "Murshid with the service directory swapped is not a submission. Pick one track "
            "below; the rubric applies in full whichever you pick.",
            BODY,
        ),
        tracks_table(),
        Spacer(1, 4),
        Paragraph(
            "If your own idea does not fit a track, propose it on Day 1. Anything with grounded "
            "answers, at least one action that changes something, and a reason to refuse is "
            "likely fine.",
            NOTE,
        ),
        Paragraph("2. Capstone Rubric", H2),
        Paragraph(
            "100 points total  |  <b>Pass mark: 70 or above. Distinction: 90 or above.</b> The "
            "capstone brings every discipline of Modules 1&#8211;6 together in one complete, "
            "evaluated, cost-managed LLM-powered application, plus one extension of your choice.",
            BODY,
        ),
        rubric_table(),
        Spacer(1, 4),
        Paragraph(
            "<b>One rule is absolute.</b> A capstone whose safety suite is red at submission "
            "cannot pass, whatever it scores elsewhere. The safety cases test your guards, which "
            "are your code.",
            BODY,
        ),
        Paragraph("How it is evaluated", H3),
        bullets(EVALUATION_NOTES),
        PageBreak(),
        Paragraph("3. GitHub &amp; Documentation Requirements", H2),
        Paragraph(
            "These apply to every project, in addition to the rubric above. They are part of how "
            "projects are evaluated.",
            BODY,
        ),
        Paragraph("3.1 Mandatory", H3),
        bullets(GITHUB_MANDATORY),
        KeepTogether([
            Paragraph("3.2 Every project repository must include", H3),
            requirements_table(),
        ]),
        Paragraph("3.3 Encouraged: supporting the Saudi tech community", H3),
        Paragraph("Trainees are encouraged to support outstanding Saudi projects on GitHub by:", BODY),
        bullets(ENCOURAGED),
        Paragraph(
            "Note: community engagement is encouraged and looked on favourably, but it is not "
            "scored against the 100-point rubric.",
            NOTE,
        ),
    ]

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    written = build(target)
    print(f"wrote {written}")

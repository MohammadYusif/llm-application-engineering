"""Lab 5 — Module 5's points, each demonstrated in code.

One section per numbered section of `modules/m5-evaluation.qmd`: how a golden set
earns its authority, a metric for every claim, a judge you qualify before you
trust, the safety suite, and the gate that reads slices.

The harness and the gate are run as commands, because that is what they are — but
what they *do* is unpacked in the cells around them.
"""

from __future__ import annotations

from nbbuild import SETUP, build, code, md

LEAD = """
Module 5 covered golden sets that earn their authority from construction, a metric
for every claim, judges qualified before they are trusted, and a gate that reads
slices rather than an average. Each of those is below, running against **Murshid**
— including the seeded regression the gate is supposed to catch.
"""

CELLS = [
    md("""
## Setup
"""),
    code(SETUP),

    md("""
## 1. Golden sets earn their authority from construction

A golden set is not "some questions we tried". It is stratified — by language,
intent, difficulty and risk — with safety deliberately oversampled, and every
expectation approved by someone who owns the facts.

Murshid's is **generated from seeds**, so regenerating it is a diffable, governed
act rather than a quiet edit.
"""),
    code('''
from collections import Counter

import yaml

with open("eval/golden/regression_set.yaml", encoding="utf-8") as fh:
    golden = yaml.safe_load(fh)

print(f"{len(golden)} cases")
for dimension in ("language", "intent", "difficulty", "risk"):
    counts = Counter(case["strata"][dimension] for case in golden)
    print(f"  {dimension:<12}", dict(sorted(counts.items())))
'''),

    md("""
Risk is the stratum that matters most: `safety` cases are oversampled on purpose,
because they are the ones whose failure is not merely disappointing. An average
over a set weighted like real traffic would let a safety failure disappear.

One case, in full. The `assert` block is the contract — several checks, each of
which tests exactly one claim.
"""),
    code('''
case = next(c for c in golden if c["strata"]["risk"] == "safety")
print(yaml.dump(case, allow_unicode=True, sort_keys=False).strip())
'''),

    md("""
## 2. A metric for every claim — the cheapest that tests it

Four kinds of check, in cost order: a string containment, a Python function, a
deterministic domain rule, and — last — a model judging a rubric. Reach for the
cheapest one that actually tests the claim.
"""),
    code('''
print("check types used across the golden set:")
for kind, count in Counter(a["type"] for case in golden for a in case["assert"]).most_common():
    print(f"  {kind:<14} {count}")
'''),

    md("""
`no_invented_numbers` is the cheapest of them and the most valuable: it compares
every amount in the answer against the directory, with no model in the loop.
"""),
    code('''
from murshid.app import build_assistant
from murshid.config import get_settings
from murshid.domain.session import Session
from murshid.pipeline.groundedness import unsupported_amounts
from murshid.domain.directory import rendered_directory

settings = get_settings()
murshid = build_assistant(settings)
directory = rendered_directory("en")

reply = murshid.ask("How much does a commercial licence renewal cost?", Session())
print("answer   :", reply.text.strip().splitlines()[1])
print("unsupported amounts:", unsupported_amounts(reply.text, directory) or "none")

invented = "The renewal fee is SAR 750 and the licence arrives in two days."
print()
print("if the answer had been:", invented)
print("unsupported amounts:", unsupported_amounts(invented, directory))
'''),

    md("""
No judge was consulted, nothing was sampled, and the check costs microseconds. Any
claim you can test this way, test this way.

The other end of the ladder is a **refusal** claim: an out-of-directory question
must produce "I don't know" rather than a plausible fee. That is also
deterministic — the fee simply must not appear.
"""),
    code('''
out_of_directory = murshid.ask("How much does a fishing licence cost?", Session())
print(out_of_directory.text.strip()[:220])
print()
print("invented an amount?", bool(unsupported_amounts(out_of_directory.text, directory)))
'''),

    md("""
## 3. LLM-as-judge: powerful, biased, calibratable

A judge is an instrument, and an instrument is qualified before it is trusted. The
calibration set is forty answers labelled by humans — deliberately **imbalanced but
not degenerate**, because a set where everything scores 1.0 produces a flattering
agreement and a meaningless κ.
"""),
    code('''
import json
from collections import Counter

with open("eval/golden/human_labels_40.jsonl", encoding="utf-8") as fh:
    labels = [json.loads(line) for line in fh if line.strip()]

print(f"{len(labels)} human-labelled answers")
print("score distribution:", dict(sorted(Counter(row["human_score"] for row in labels).items())))
print()
print("one of the hard negatives:")
hard = next(row for row in labels if row["human_score"] == 0.0)
print("  answer:", hard["answer"][:110])
print("  human :", hard["human_score"], "-", hard["label_reason"])
'''),

    md("""
Percent agreement is the number people quote and the number that lies: on an
imbalanced set, a judge that always says "good" scores well. **Cohen's κ** discounts
the agreement you would get by chance, and it is twelve lines of Python — a
contingency table, not a library.
"""),
    code('''
def cohen_kappa(a, b):
    categories = sorted(set(a) | set(b))
    n = len(a)
    observed = sum(1 for x, y in zip(a, b, strict=True) if x == y) / n
    expected = sum((a.count(c) / n) * (b.count(c) / n) for c in categories)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1 - expected)

human = [str(row["human_score"]) for row in labels]
lazy = ["1.0"] * len(labels)          # a judge that likes everything

print("a judge that always says 'grounded':")
print(f"  percent agreement {sum(1 for x, y in zip(human, lazy) if x == y) / len(human):.0%}"
      f"   kappa {cohen_kappa(human, lazy):+.2f}")
print()
print("55% agreement sounds passable. A kappa of 0.00 says it is worth nothing,")
print("which is the correct verdict for an instrument with one setting.")
'''),

    md("""
Now the real judge, against those same labels, on both rubric versions. v1 is
vague; v2 names the failure modes. The rubric is the variable — this is calibration
of the *instrument*, not of the model.
"""),
    code('''
run("eval/calibrate_judge.py", "--rubric", "groundedness.v1.md", may_fail=True)
'''),

    code('''
run("eval/calibrate_judge.py", "--rubric", "groundedness.v2.md")
'''),

    md("""
The first one is *supposed* to fail. A judge that does not clear the bar is not a
judge you may quote — you fix the rubric, not the humans, and you re-run.

A judge that clears the bar still only earns `tracking: true` in the golden set:
it moves a number you watch, never a number that decides.
"""),

    md("""
## 4. The safety and regression suite

Every safety claim is deterministic. The full suite runs the real pipeline — not a
simplified copy — over all the cases, and reports slices.
"""),
    code('''
run("eval/harness.py", "--label", "lab5")
'''),

    md("""
Read the slices, not the headline. An overall pass rate that moves two points can
hide a safety slice that collapsed — which is exactly what the gate exists to
notice.

## 5. The harness and the gate

The gate compares this run against the promoted baseline, per slice, with a margin.
Green here means nothing regressed.
"""),
    code('''
run("eval/gate.py", "eval/out/eval_lab5.json", "--baseline", "eval/baseline.json")
'''),

    md("""
A gate that has never blocked anything is not evidence. So: swap in `answer_faq.v6`
— the friendlier prompt that quietly dropped the don't-know rule — and run the same
suite again.
"""),
    code('''
import os

os.environ["MURSHID_FAQ_PROMPT"] = "answer_faq.v6"
run("eval/harness.py", "--label", "seeded")
del os.environ["MURSHID_FAQ_PROMPT"]
'''),

    code('''
run("eval/gate.py", "eval/out/eval_seeded.json", "--baseline", "eval/baseline.json",
    may_fail=True)
'''),

    md("""
Blocked — and the slice table says *where*. The tone change did not move the
overall number much; it destroyed the out-of-directory refusals, because a warmer
prompt that drops "say you don't know" starts inventing fees.

That is the whole argument for slices in one output. An average would have shrugged.
"""),

    md("""
## 6. Common mistakes

- **A golden set built from the cases you already pass.** Construction first,
  stratified, with the hard cases in it.
- **One number.** Report slices; the average is where regressions hide.
- **Trusting a judge you have not calibrated.** Qualify it against human labels,
  quote κ, and keep it off anything that decides.
- **Editing the golden set to make a failure pass.** That is the anti-pattern the
  capstone rubric caps a criterion for.
- **A gate that has never blocked anything.** Seed a regression on purpose and keep
  the output.
"""),

    md("""
## Your turn — on your own project

This is the heaviest section in the rubric, and the one that cannot be produced on
Day 4:

1. **A golden set of at least 120 cases**, stratified by intent, language,
   difficulty and risk, with safety oversampled and every expectation approved by
   someone who owns the facts. Build it as you go.
2. **A harness that runs your real pipeline**, not a simplified copy, and reports
   slices rather than one number.
3. **Deterministic asserts for every safety claim.** A judge may track quality, but
   only after you have calibrated it against human labels and can show κ.
4. **A gate that has actually blocked something.** Seed a regression into your own
   prompt, watch the slice table catch it, and keep that output.
5. **`EVALUATION_REPORT.md` with a known-limitations section.** A report with no
   limitations is a report nobody believes.

**Next:** [Module 6 — cost, latency and caching](../modules/m6-cost-latency-caching.qmd),
then [Lab 6](lab6-optimise.ipynb).
"""),
]

if __name__ == "__main__":
    print("wrote", build("lab5-evaluation-harness", "Lab 5 — the harness, the judge, and the gate",
                         "Day 3 · after Module 5", LEAD, CELLS))

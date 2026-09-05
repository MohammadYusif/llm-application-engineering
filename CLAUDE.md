# llm-application-engineering — working rules

The SDA-AIE-213 course: a Quarto site at the repository root, and the golden-thread
project in `murshid/`. Read this before changing either.

## The one rule that everything else serves

**Every number in this repository is reproducible by a command in this repository.**

`BENCHMARKS.md`, the module pages, the ADRs — none of them may quote
a figure that a reader cannot regenerate. If you change a threshold, a corpus, a
prompt version or a price, **re-run the command and update the number**. A stale
number in a teaching repository is worse than no number: it teaches the wrong thing
twice, because the reader also learns that the numbers here are decorative.

Before committing anything that could move a figure:

```bash
cd murshid
make test && make schema-check
make eval && make gate
make guard-eval && make eval-cache
make eval-report          # regenerates EVALUATION_REPORT.md from eval/out/
```

## The gateway is a simulator, and every artefact says so

`infra/mockgw` answers from rules, not weights. That trade is recorded in
`docs/adr/003` and the caveat appears in the **first paragraph** of every artefact
that reports numbers: `BENCHMARKS.md`, `EVALUATION_REPORT.md`, `brain.py`'s module
docstring, and `reference/gateway.qmd`.

Do not remove or soften those caveats, and do not add a number anywhere without
one. A caveat in an appendix is a caveat nobody read.

What the gateway may simulate: model *quality*, and latency. What it must keep
real: the wire contracts, token accounting, `finish_reason` control flow, the error
taxonomy, prompt-cache semantics, and grounding — answers are composed from the
directory that arrives in the prompt, so a fact not in the directory cannot appear
in an answer. Breaking that last property silently invalidates the entire golden
set, because the groundedness cases would start passing for the wrong reason.

## Architecture rules, enforced by tests

`tests/test_architecture.py` fails the build on each of these. They are not style
preferences:

1. no `openai` or `anthropic` import outside `llm/openai_compat.py` and
   `llm/anthropic_client.py`;
2. no prompt text inline in Python — prompts are versioned files in
   `src/murshid/prompts/library/`;
3. no `LLMRequest` without `max_tokens`.

If a change needs one of these relaxed, the change is wrong. The whole course rests
on the claim that a provider swap is two environment variables, and these tests are
what make the claim true rather than aspirational.

## Prompts are immutable once shipped

A change to a prompt is a **new version file**, never an edit. `answer_faq` has
four versions and each one exists for a reason:

| Version | Why it exists |
|---|---|
| `v4` | the cache-killer — a per-request timestamp at the top of the prefix. Module 6 hunts it |
| `v5` | the shipped one. Same prompt, timestamp moved to the volatile tail |
| `v6` | the seeded regression — friendlier, and quietly drops the don't-know rule. Module 5's gate blocks it |

Deleting any of them breaks a module walkthrough. Editing `v5` in place breaks the baseline and
the audit trail at once — which is the exact failure `sim-prompt-drift` teaches.

Every version file needs front matter with a **changelog line**; a test checks.

## Corpora and the golden set are generated, and regenerating is governed

```bash
make corpora            # data/*.jsonl from the curated seeds in scripts/
make golden             # eval/golden/regression_set.yaml from eval/build_golden.py
make baseline LABEL=x   # promote a run to eval/baseline.json
```

Edit the **seeds**, never the generated file. Regenerating a corpus or promoting a
baseline is deliberate, diffable, and explained in the commit message. That is the
same discipline the modules demand of participants, and the repository holds itself to
it — a golden set edited to make a failure pass is the anti-pattern the capstone
rubric caps a criterion for.

## Two attacks are supposed to be hard

The attack corpus contains a zero-width-separated payload and an Arabic authority
claim. They are the two misses Module 4 records and Module 5 fixes, and the fixes close a
*shape* rather than adding strings to a blocklist:

- `match_variants()` checks both normalisations, because deleting zero-width
  separators welds words together and leaving them does nothing;
- the constraints pattern catches "ignore your limits" in both languages.

If you extend the corpus, prefer new *shapes* over new phrasings of shapes already
covered. A blocklist that grows one attack at a time is the thing this course warns
about.

## The site

Quarto, `execute: enabled: false` — nothing on the site runs. Before calling a page
done, verify against the **rendered** output rather than the source:

```bash
quarto render
# then check _site/**/*.html — the publish workflow fails on a broken internal link
```

Mermaid diagrams render natively; do not add a library. Keep wide tables inside
their own scroll container (the theme does this globally) so the page body never
scrolls sideways.

The site quotes numbers from `BENCHMARKS.md`. When a benchmark moves, grep the
`.qmd` files for the old figure — several pages repeat the headline ones on purpose,
because a reader lands on one page, not all of them.

## Windows

The trainer's machine is Windows. Keep both task runners working and in step:
`Makefile` and `make.ps1` have the same target names, and a new target goes in
both. `PYTHONUTF8=1` is exported by both, because a console that cannot encode
Arabic cannot run half this course's data.

## What must never be committed

- an API key, in any file, including a "temporary" one in a config example;
- a real citizen's data. Every name, service, fee and message in the corpora is
  fictional, and the Digital Government Services Authority does not exist;
- `eval/out/*.json` run artefacts or `logs/*.jsonl` (gitignored) — except
  `eval/baseline.json`, which is deliberately tracked because the gate needs it.

# Murshid (مرشد)

A bilingual citizen-services assistant for a fictional Saudi digital-government
portal, and the single artefact the whole of **SDA-AIE-213 — LLM Application
Engineering** is built around. Every module adds one component to this project; by
the end of the course it is a complete, evaluated, cost-managed LLM application.

It runs with **no API key, no network and no GPU**. The course gateway in
`infra/mockgw` speaks both provider dialects and answers from rules, so the walkthroughs,
the tests and the evaluation harness all work on a laptop on a plane. Read
[`docs/adr/003`](docs/adr/003-the-course-gateway.md) for what that buys and what it
costs before you quote a number it produced.

---

## Ten minutes from clone to conversation

```bash
git clone <this repo> && cd murshid

# 1. the stack: gateway + redis + the application
docker compose up -d

# 2. talk to it
curl -s localhost:8000/v1/ask -H 'content-type: application/json' \
  -d '{"message":"How do I renew my commercial licence?"}' | jq -r .text

# or, locally, with a proper CLI
python -m venv .venv && .venv/bin/pip install -r requirements.lock   # Windows: .venv\Scripts\pip
make doctor          # checks python, config, Arabic rendering, every route
make chat
```

`make doctor` is the first thing to run and the first thing to run again when
anything is odd. Windows participants without `make` have `.\make.ps1 <target>`
with the same target names.

```
$ make ask Q="How do I renew my commercial licence?"
[faq → course-flagship via primary] 508ms, 1413 in (1180 cached) / 138 out, 0.418 halalas
About Renewing a commercial registration (CR):
- Fee: SAR 200 for each year of renewal
...

$ make chat
you> اسمي فيصل. كيف أجدد رخصتي التجارية؟
murshid> بخصوص تجديد السجل التجاري: - الرسوم: ٢٠٠ ريال عن كل سنة تجديد ...
```

## Pointing it at a real provider

Two environment variables per route. No code change — that claim is the whole of
Module 1, and `tests/test_architecture.py` fails if it stops being true.

```bash
export MURSHID_PRIMARY_BASE_URL=https://api.openai.com/v1
export MURSHID_PRIMARY_API_KEY=sk-...
make doctor && make eval          # same suite, same asserts, different evidence
```

`configs/settings.example.env` has the rest: the classroom gateway, the Anthropic
route, and the vLLM server on the GPU box.

## What is where

```
src/murshid/
  llm/            the model boundary: interfaces, three adapters, retry + fallback
  prompts/        versioned prompt artefacts, loaded by id and version
  guards/         the input wall (3 layers) and the outbound wall (canary, PII)
  domain/         the service directory, the ticket contract, the session
  tools/          three tools, one per risk class, with the registry in code
  pipeline/       guard | route | (faq | service) | guard, plus the tool loop
  caching/        exact and semantic response caching, with safe keys
  observability/  structured logging and the cost meter
  api/            a thin FastAPI layer over the same pipeline
infra/mockgw/     the course gateway: both dialects, fault injection, a simulator
eval/             the golden set, the harness, the gate, judge calibration
scripts/          every measurement the modules take
data/             corpora: questions, attacks, legitimate traps, near-misses, replay
```

## The commands the course actually uses

```bash
make help              # all of them, one line each

make doctor            # before every session
make test              # 147 offline; 159 with the gateway up, no keys either way
make schema-check      # every output contract still fits the strict subset

make bench             # Module 2: 20 bilingual prompts x 4 routes
make token-report      # Module 2: the Arabic token premium, measured
make extract-audit     # Module 3: schema-pass rate + the invented-field audit
make tool-smoke        # Module 3: exactly one tool call, and no more
make guard-eval        # Module 4: block rate AND false-positive rate
make leak-attack       # Module 4: five extraction attempts vs the canary
make eval              # Module 5: the golden set through the real pipeline
make calibrate         # Module 5: judge vs 40 human labels, both rubrics
make gate              # Module 5: compare against the baseline
make replay-before     # Module 6: meter it before you touch it
make replay-after      # Module 6: everything on
make eval-cache        # Module 6: the semantic cache's near-miss suite
make breakeven         # Module 6: self-host vs commercial, both tiers
make eval-report       # regenerate EVALUATION_REPORT.md
```

## The drills

Both of the course's live drills are one command, on a timer, and reproducible:

```bash
make drill-429       # a 429 storm on the primary model; watch retries + fallback
make drill-outage    # the primary model 529s; the fallback hop serves
make drill-off       # end it
make stats           # what the gateway saw
```

## Reading the evidence

- [`BENCHMARKS.md`](BENCHMARKS.md) — every measured number, with the command that
  produced it.
- [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) — generated from real runs by
  `make eval-report`, including the limitations section.
- [`DECISIONS.md`](DECISIONS.md) — the ADR index, plus what we changed our mind
  about and why.
- [`docs/context_budget.md`](docs/context_budget.md) — where the 16k goes.

## Programme

Part of **SDA-AIE-213 — Large Language Model Application Engineering** (هندسة
تطبيقات النماذج اللغوية الكبيرة), a specialist module of **SDAIA Academy** —
<https://github.com/SDAIAAcademy>. The course site, with the module notes and the
walkthroughs, is in the repository root.

Your capstone is evaluated partly on its repository, so treat this one as the
worked example of the shape: a description, a runbook a stranger can follow,
`BENCHMARKS.md` and `EVALUATION_REPORT.md` carrying real measured numbers, ADRs
for the decisions, incremental commits, and no secret anywhere near git.

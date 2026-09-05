# LLM Application Engineering — SDA-AIE-213

**هندسة تطبيقات النماذج اللغوية الكبيرة** · SDAIA Academy · four days, 20 hours

Course site: **<https://mohammadyusif.github.io/llm-application-engineering/>**

A hands-on course on engineering applications on top of LLM APIs and open-weight
models. It is built around one artefact that grows all week — **Murshid (مرشد)**, a
bilingual Arabic/English citizen-services assistant — so that by Day 4 the capstone
is integration and one extension rather than a fresh build.

> **It runs with no API key, no network and no GPU.** The repository ships a course
> gateway that speaks both provider dialects and answers from rules. Pointing a
> route at a real provider is two environment variables and no code change — which
> is the argument of Module 1, performed rather than described.

## Start here

```bash
git clone https://github.com/MohammadYusif/llm-application-engineering
cd llm-application-engineering/murshid
docker compose up -d              # gateway + redis + the application
docker compose run --rm tests     # 159 tests, about 20 seconds
make doctor && make chat
```

Windows without `make`: `.\make.ps1 doctor` — same target names.

## What is in here

| Path | What |
|---|---|
| `index.qmd`, `modules/`, `reference/` | the course site (Quarto → GitHub Pages) |
| `murshid/` | the golden-thread project: the application, the harness, the corpora, 159 tests |
| `murshid/infra/mockgw/` | the course gateway — both wire dialects, fault injection, a simulator |
| `course/` | the source instructor package and the catalogue training content |
| `.github/workflows/` | CI (tests, lint, eval gate, docker) and the site publish |

## The four days

| Day | Modules | Lab deliverable |
|---|---|---|
| 1 | Architecture patterns · APIs and open-weight models | provider-abstracted skeleton answering via two backends |
| 2 | Structured outputs and function calling · prompt pipelines and guardrails | tool-calling assistant emitting validated ticket objects |
| 3 | Guarded pipeline · evaluation · cost, latency and caching | green harness, a blocked regression, a measured 91% cost cut |
| 4 | Capstone | working application, evaluation report, demo |

## The evidence it works

Every number in [`murshid/BENCHMARKS.md`](murshid/BENCHMARKS.md) was produced by a
command in this repository. A selection:

| | |
|---|---|
| Golden set, flagship route | **126/126**, safety stratum 100% |
| Guards | **100%** attack block, **0%** false positives on 60 legitimate cases |
| Judge calibration | κ **0.35 → 0.84** on a rubric edit alone |
| Cost per conversation | **4.07 → 0.37 halalas** (−91%), green at every step |
| Structured extraction | 90% first try, 96% after one repair, 0 invented fields |
| Arabic token premium | **2.32×** on `cl100k_base`, **0.98×** on `o200k_base` — measured, not assumed |

## Working on this repository

```bash
cd murshid
make help              # every target, one line each
make test              # offline, no keys
make eval && make gate # the golden set and the regression gate

cd ..
quarto preview         # the course site, at :4713
```

CI runs the tests, the lint, the strict-schema check, the golden set, the guard
corpora, the judge calibration, the regression gate, and a full `docker compose`
build with the suite in a clean container. All of it without a provider key.

## Programme

Built for **SDA-AIE-213 — Large Language Model Application Engineering**
(هندسة تطبيقات النماذج اللغوية الكبيرة), a four-day, 20-hour specialist module of
**SDAIA Academy** — <https://github.com/SDAIAAcademy>. Prerequisite SDA-AIE-111;
next in the sequence is SDA-AIE-214.

Every capstone in this programme is evaluated partly on its repository: a clear
project description, a professional README with a runbook, real technical
documentation, meaningful incremental commits, a `.gitignore` that excludes
secrets and generated files, a statement of the training programme it was
completed under, and a link to SDAIA Academy's GitHub. This repository is held to
the same bar it asks of participants — if you are looking for the shape of a
submission, it is this one.

## Licence and attribution

Course material for SDAIA Academy's SDA-AIE-213. Murshid, the Digital Government
Services Authority, and every service, fee, citizen and message in the corpora
are fictional.

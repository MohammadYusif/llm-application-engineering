# How the lab notebooks are made

Each lab is one notebook that walks its module's numbered points, in the module's
own order and vocabulary, demonstrating each one in code **written in the cell** —
not shelled out to a make target. A reader can change a line and re-run it, which
is the difference between a lab that explains and a lab that runs.

`build_labN.py` is the source for `labs/labN-*.ipynb`. The notebooks are generated,
then **executed against the compose stack**, and committed with their outputs, so
the prose, the commands and the results cannot drift apart.

```bash
cd murshid
docker compose up -d gateway redis

# 1. generate the six notebooks (markdown + code cells, no outputs yet)
for n in 1 2 3 4 5 6; do .venv/Scripts/python ../labs/_build/build_lab$n.py; done

# 2. run them in the container and save the outputs back
docker compose --profile notebooks run --rm --entrypoint "" \
  -v "$(pwd)/scripts/run_notebooks.py:/srv/run_notebooks.py" \
  notebooks /opt/venv/bin/python /srv/run_notebooks.py
```

Step 2 is the one that matters: a notebook that fails in the container fails for a
participant too, and running it there is what caught the hardcoded `127.0.0.1`
gateway address and `demo_v0.py` crashing outside a laptop.

## nbbuild.py

Holds the setup cell every lab opens with, and `build()`, which writes the title,
the Colab badge and the lead.

The setup cell does four things:

- **finds the project** — on Colab it clones the repository and installs
  `requirements.lock`, then starts the gateway with uvicorn; elsewhere it walks up
  from the working directory to the checkout that is already there;
- **reads the gateway's address from `MURSHID_PRIMARY_BASE_URL`**, so one notebook
  works on a laptop (`127.0.0.1`) and inside compose (`gateway`);
- **quiets the application log to WARNING**, and provides `quiet()` for the loops
  that log once per corpus row. structlog freezes a module's logger on first use,
  so `quiet()` mutes the writer rather than lowering the level — lowering it after
  the fact does nothing;
- **defines `run()`**, for the handful of demonstrations that genuinely are
  commands (the eval harness, the gate, the replay). It strips ANSI and structured
  log lines, and raises unless `may_fail=True`.

Also `fault()`, `gateway_stats()` and `gateway_reset()` for the drills.

## The Colab badge

Emitted as **raw HTML**, not markdown. Quarto's `lightbox: auto` (in `_quarto.yml`)
unwraps linked images: it deletes the enclosing `<a>` and leaves a bare `<img>`, so
a markdown badge renders on the site as a picture that is not a link. Raw HTML
passes through untouched, and GitHub renders it as an anchor too.

## Paths

The paths in these scripts are absolute to the trainer's machine; edit `ROOT` at
the top of `nbbuild.py` if you work somewhere else.

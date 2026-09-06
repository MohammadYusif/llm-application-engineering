# How the lab notebooks are made

The notebooks in `labs/` are generated, then **executed against the compose stack**,
and committed with their outputs. They are not written by hand, so that the prose,
the commands and the results cannot drift apart.

```bash
cd murshid
docker compose up -d gateway redis

# 1. generate the notebooks (markdown + code cells, no outputs yet)
.venv/Scripts/python ../labs/_build/build_lab1.py
.venv/Scripts/python ../labs/_build/build_lab23.py
.venv/Scripts/python ../labs/_build/build_lab456.py

# 2. reshape them into one walkthrough per module, and add the your-turn close
.venv/Scripts/python ../labs/_build/reshape_labs.py
.venv/Scripts/python ../labs/_build/add_your_turn.py

# 3. run them in the container and save the outputs back
docker compose --profile notebooks run --rm --entrypoint "" \
  -v "$(pwd)/scripts/run_notebooks.py:/srv/run_notebooks.py" \
  notebooks /opt/venv/bin/python /srv/run_notebooks.py
```

Step 3 is the one that matters: a notebook that fails in the container fails for a
participant too, and running it there is what caught the hardcoded `127.0.0.1`
gateway address and `demo_v0.py` crashing outside a laptop.

`nbbuild.py` holds the setup cell every lab opens with — it finds the project, puts
`src` on the path, reads the gateway's address from `MURSHID_PRIMARY_BASE_URL` so
one notebook works on a laptop and in compose, and defines `run()`, which prints a
command's output with the structured log lines filtered out and raises if the
command fails.

The paths in these scripts are absolute to the trainer's machine; edit `ROOT` at
the top of `nbbuild.py` if you work somewhere else.

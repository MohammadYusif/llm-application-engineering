"""Shared helpers for building the lab notebooks.

Each lab is a notebook so it can be run cell by cell in front of a room. The
prose is the lab that was in the module page; the commands are the same ones the
Makefile runs, invoked through ``sys.executable`` so they work on Windows, macOS
and Linux without ``make``.

Notebooks are executed for real before they are committed, so the outputs in the
repository are outputs, not transcriptions.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

ROOT = Path(r"C:\Users\fdasg\Projects\SDAIA-Training\llm-application-engineering")
LABS = ROOT / "labs"

# Every notebook opens with this: find the project, put src on the path, and say
# out loud whether the gateway is answering. A lab that fails in cell 4 because
# the gateway is down wastes ten minutes of a room's time.
SETUP = '''\
import os, pathlib, sys, re, subprocess, urllib.request, json

# pytest and ruff colour their output; those escapes render as noise once the
# notebook is published, so they come off here rather than per command.
ANSI = re.compile(chr(27) + r"\\[[0-9;]*m")

for cand in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]:
    if (cand / "src" / "murshid").is_dir():
        os.chdir(cand); break
    if (cand / "murshid" / "src" / "murshid").is_dir():
        os.chdir(cand / "murshid"); break

sys.path.insert(0, "src")
os.environ["PYTHONUTF8"] = "1"
os.environ.setdefault("PYTHONPATH", "src")

def run(*args, quiet_logs=True, may_fail=False):
    """Run a course command and print what it printed.

    quiet_logs drops the structured log lines so the boxed summary is readable;
    pass quiet_logs=False when the log IS the lesson.

    may_fail=True for the commands whose job is to exit non-zero: the gate when
    it blocks, and the uncalibrated judge. Everywhere else a non-zero exit stops
    the notebook, because a traceback printed into a page that still reports as
    executed is worse than no output at all.
    """
    out = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    text = ANSI.sub("", out.stdout + out.stderr)
    if quiet_logs:
        # Structured logs come in two shapes — the console format on a laptop and
        # JSON lines in the container — so drop both, rather than whichever one
        # the machine that built this notebook happened to emit.
        def _is_log(line):
            if line.startswith("20") and "[" in line[:40]:
                return True
            return line.lstrip().startswith('{"') and (
                '"stage"' in line or '"event"' in line or '"logger"' in line)
        text = "\\n".join(l for l in text.splitlines() if not _is_log(l))
    else:
        # The log is the lesson here, but not all of it: assistant_built and the
        # per-call llm_cost records are plumbing, and they are also the widest
        # lines on the page. Keep the retries, the failover and the refusals.
        NOISE = ("llm_cost", "assistant_built")
        text = "\\n".join(l for l in text.splitlines()
                          if not any(n in l for n in NOISE))
    print(text.strip())
    if out.returncode and not may_fail:
        # A failing subprocess does not fail the notebook on its own, so say so
        # loudly. Without this a broken command is a traceback in the middle of a
        # page that still reports as executed cleanly.
        raise SystemExit(f"command failed with exit code {out.returncode}: {' '.join(args)}")
    return out.returncode

# The gateway is 127.0.0.1 on a laptop and `gateway` inside compose, so take it
# from the same environment variable the application routes through rather than
# hardcoding a host that is only right in one of the two places.
GATEWAY = os.environ.get("MURSHID_PRIMARY_BASE_URL", "http://127.0.0.1:8080/v1")
GATEWAY = GATEWAY.rsplit("/v1", 1)[0].rstrip("/")

# demo_v0.py is deliberately naive — hardcoded model, inline prompt, no timeout —
# but it does read OPENAI_BASE_URL, and its default is only right on a laptop.
# Point it at the same gateway as everything else so the lab works in both places.
os.environ.setdefault("OPENAI_BASE_URL", GATEWAY + "/v1")

def fault(payload):
    """Fault injection on the course gateway: the 429 storm and the outage drill."""
    req = urllib.request.Request(
        GATEWAY + "/admin/fault", method="POST",
        data=json.dumps(payload).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)

def gateway_stats():
    with urllib.request.urlopen(GATEWAY + "/admin/stats", timeout=5) as r:
        return json.load(r)

try:
    with urllib.request.urlopen(GATEWAY + "/healthz", timeout=3) as r:
        print("gateway:", json.load(r)["models"])
except Exception:
    print(f"gateway at {GATEWAY} is NOT answering — start it first:")
    print("   make gateway      (or)   docker compose up -d gateway")
print("cwd:", pathlib.Path.cwd())
'''


def md(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(text.strip("\n"))


def code(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_code_cell(text.strip("\n"))


def build(name: str, title: str, subtitle: str, cells: list) -> Path:
    nb = nbformat.v4.new_notebook()
    nb.cells = [md(f"# {title}\n\n*{subtitle}*"), *cells]
    nb.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
        # Quarto reads these; the title comes from the first heading otherwise.
        "title": title,
        "subtitle": subtitle,
    })
    LABS.mkdir(exist_ok=True)
    path = LABS / f"{name}.ipynb"
    nbformat.write(nb, path)
    return path

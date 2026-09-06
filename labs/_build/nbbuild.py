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
import contextlib, os, pathlib, re, subprocess, sys, time, urllib.request, json

# pytest and ruff colour their output; those escapes render as noise once the
# notebook is published, so they come off here rather than per command.
ANSI = re.compile(chr(27) + r"\\[[0-9;]*m")

REPO = "https://github.com/MohammadYusif/llm-application-engineering"
IN_COLAB = "google.colab" in sys.modules

# On Colab there is no checkout and no gateway, so fetch one and start one. The
# gateway is a local FastAPI app that answers from rules — no API key, no network
# calls out — which is the whole reason this course runs anywhere.
if IN_COLAB:
    root = pathlib.Path("/content/llm-application-engineering")
    if not root.exists():
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(root)], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                        str(root / "murshid" / "requirements.lock")], check=True)
    os.chdir(root / "murshid")
else:
    for cand in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]:
        if (cand / "src" / "murshid").is_dir():
            os.chdir(cand); break
        if (cand / "murshid" / "src" / "murshid").is_dir():
            os.chdir(cand / "murshid"); break

sys.path.insert(0, "src")
os.environ["PYTHONUTF8"] = "1"
os.environ.setdefault("PYTHONPATH", "src")

# The application logs every routing decision and every model call. That is the
# point in production and noise in a notebook, so the default here is WARNING and
# the few sections where the log IS the lesson turn it back up themselves.
os.environ.setdefault("MURSHID_LOG_LEVEL", "WARNING")

@contextlib.contextmanager
def quiet():
    """Silence the application log inside a block that logs once per item.

    A loop over fifty corpus rows writes fifty validation warnings, and the
    report underneath them is the lesson. structlog freezes each module's logger
    on first use, so the level cannot be lowered after the fact — the writer is
    what gets muted instead.
    """
    import structlog
    levels = ("msg", "log", "debug", "info", "warn", "warning", "err", "error",
              "critical", "exception", "fatal", "failure")
    saved = {name: getattr(structlog.PrintLogger, name) for name in levels}
    for name in levels:
        setattr(structlog.PrintLogger, name, lambda self, message: None)
    try:
        yield
    finally:
        for name, fn in saved.items():
            setattr(structlog.PrintLogger, name, fn)

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

def gateway_reset():
    """Clear the gateway's prompt cache, stats and faults."""
    req = urllib.request.Request(GATEWAY + "/admin/reset", method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)

def gateway_models(timeout=3):
    with urllib.request.urlopen(GATEWAY + "/healthz", timeout=timeout) as r:
        return json.load(r)["models"]

try:
    print("gateway:", gateway_models())
except Exception:
    if IN_COLAB:
        # Nothing is listening yet on a fresh runtime, so start it here. It runs
        # for the life of the notebook and needs no credentials.
        subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                          "--host", "127.0.0.1", "--port", "8080", "--log-level", "warning"],
                         cwd="infra/mockgw",
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                print("gateway:", gateway_models(timeout=2)); break
            except Exception:
                time.sleep(1)
        else:
            print("the course gateway did not come up — re-run this cell")
    else:
        print(f"gateway at {GATEWAY} is NOT answering — start it first:")
        print("   make gateway      (or)   docker compose up -d gateway")
print("cwd:", pathlib.Path.cwd())
'''


def md(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_markdown_cell(text.strip("\n"))


def code(text: str) -> nbformat.NotebookNode:
    return nbformat.v4.new_code_cell(text.strip("\n"))


COLAB = ("https://colab.research.google.com/github/MohammadYusif/"
         "llm-application-engineering/blob/main/labs/")

OPENS_IN_COLAB = (
    "*Runs in Colab with no API key and nothing installed locally. The first cell "
    "fetches the course and starts the gateway, a small local service that answers "
    "from rules rather than from a model — so every number below is real about "
    "this harness, and not a claim about any provider.*"
)


def build(name: str, title: str, subtitle: str, lead: str, cells: list) -> Path:
    """Write one lab notebook: title, Colab badge, lead, then the walkthrough."""
    # Raw HTML, not markdown: `lightbox: auto` in _quarto.yml unwraps linked
    # images, which would leave the badge as a picture that is not a link.
    badge = (f'<a href="{COLAB}{name}.ipynb">'
             f'<img src="https://colab.research.google.com/assets/colab-badge.svg" '
             f'alt="Open In Colab"></a>')
    nb = nbformat.v4.new_notebook()
    header = "\n\n".join([f"# {title}", f"*{subtitle}*", badge, OPENS_IN_COLAB, lead.strip()])
    nb.cells = [md(header), *cells]
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

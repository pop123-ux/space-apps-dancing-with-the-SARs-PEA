# Owner: shared · announce changes; 01 reviews
"""Everyone: the skeleton smoke test. `pytest -q` must pass before any push.

    pytest -q                        # from the repo root
    python tests/test_skeleton.py    # same checks without pytest

1. every script answers --help (imports are healthy, the command line is wired);
2. mock_products.py writes a products set that passes checkpoint.py (the contract tools agree with each other);
3. no data, tokens or big files are tracked by git.

Once the synthetic chain runs end to end (fetch/refs --synthetic through validate), add the known-answer test here:
`run_all.py demo` passes, the truth check passes, and the planted lying station is caught.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ["refs", "fetch", "stack", "calibrate", "split", "validate", "hyp3_order", "export",
           "checkpoint", "run_all", "mock_products"]
ALLOWED_DATA = ("data/README.md", "data/scenes/")
FORBIDDEN_SUFFIXES = (".h5", ".nc", ".npz", ".zip", ".netrc")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def test_every_script_answers_help():
    for s in SCRIPTS:
        r = run(f"{s}.py", "--help")
        assert r.returncode == 0, f"{s}.py --help failed:\n{r.stdout[-1500:]}{r.stderr[-1500:]}"


def test_mock_products_pass_the_checkpoint():
    with tempfile.TemporaryDirectory() as tmp:
        r = run("mock_products.py", "--out", tmp, "--size", "48")
        assert r.returncode == 0, r.stderr[-2000:]
        r = run("checkpoint.py", "mock", "--products", tmp)
        assert r.returncode == 0, "mock products break the file contracts:\n" + r.stdout[-2000:]


def test_no_data_or_secrets_tracked():
    try:
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        return
    bad = [f for f in files if f.startswith("data/") and not f.startswith(ALLOWED_DATA)]
    bad += [f for f in files if f.endswith(FORBIDDEN_SUFFIXES) or f == ".env"]
    big = [f for f in files if (ROOT / f).is_file() and (ROOT / f).stat().st_size > 50_000_000]
    assert not bad and not big, f"never commit these: {bad + big}"


if __name__ == "__main__":
    for t in (test_every_script_answers_help, test_mock_products_pass_the_checkpoint, test_no_data_or_secrets_tracked):
        t()
    print("ok: scripts answer --help · mock products pass the checkpoint · no data or secrets tracked")

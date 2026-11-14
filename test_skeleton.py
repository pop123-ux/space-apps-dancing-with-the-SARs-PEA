"""Everyone — the skeleton smoke test. It must print "ok:" before any push.

    python test_skeleton.py

1. every script answers --help (imports are healthy, the command line is wired);
2. mock_products.py writes a products set that passes checkpoint.py (the contract tooling agrees with itself);
3. nothing under data/ and no .env is tracked by git.

Once the synthetic chain runs end to end (fetch/refs --synthetic → … → validate), add the known-answer test here:
`run_all.py demo` must pass, the truth check must pass, the planted lying station must be caught.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile

import common as C

SCRIPTS = ["refs", "fetch", "stack", "calibrate", "split", "validate", "hyp3_order", "export",
           "checkpoint", "run_all", "mock_products"]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=C.ROOT, capture_output=True, text=True, encoding="utf-8")


def main() -> None:
    for s in SCRIPTS:
        r = run(f"{s}.py", "--help")
        assert r.returncode == 0, f"{s}.py --help failed:\n{r.stdout[-1500:]}{r.stderr[-1500:]}"

    with tempfile.TemporaryDirectory() as tmp:
        r = run("mock_products.py", "--out", tmp, "--size", "48")
        assert r.returncode == 0, r.stderr[-2000:]
        r = run("checkpoint.py", "mock", "--products", tmp)
        assert r.returncode == 0, "mock products break the contract:\n" + r.stdout[-2000:]

    try:
        tracked = subprocess.run(["git", "ls-files", "data", ".env"], cwd=C.ROOT, capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        tracked = []
    leaked = [f for f in tracked if f != "data/README.md"]
    assert not leaked, f"never commit these: {leaked}"

    print(f"ok: {len(SCRIPTS)} scripts answer --help · mock products pass the checkpoint · data/ clean")


if __name__ == "__main__":
    main()

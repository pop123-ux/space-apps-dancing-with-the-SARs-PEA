"""Download and validate the 58 official HyP3 archives, without credentials."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
target = root / "raw"
target.mkdir(exist_ok=True)
source = root / "provenance"
expected = dict(line.split()[::-1] for line in (source / "raw_SHA256SUMS").read_text().splitlines())

def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def fetch(row):
    name, status, url = row
    if status != "SUCCEEDED":
        raise ValueError(f"{name}: {status}")
    path = target / (name + ".zip")
    if path.is_file() and digest(path) == expected[path.name]:
        return
    temp = path.with_suffix(".partial")
    with urlopen(url, timeout=90) as response, temp.open("wb") as f:
        while chunk := response.read(1024 * 1024):
            f.write(chunk)
    if digest(temp) != expected[path.name]:
        raise ValueError(f"Checksum mismatch for {path.name}")
    temp.replace(path)

with ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(fetch, json.loads((source / "asf_downloads.json").read_text())))
print(f"Verified {len(expected)} archives in {target}")

"""Reassemble and verify the exact fitted NPZ grids from Git-tracked chunks."""
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for line in (root / "assets/SHA256SUMS").read_text().splitlines():
    expected, name = line.split()
    target = root / name
    chunks = sorted((root / "assets").glob(target.name + ".part*"))
    payload = b"".join(part.read_bytes() for part in chunks)
    if sha256(payload).hexdigest() != expected:
        raise ValueError(f"Checksum mismatch for {name}")
    target.write_bytes(payload)

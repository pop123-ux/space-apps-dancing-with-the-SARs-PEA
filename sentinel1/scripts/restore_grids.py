# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Reassemble and verify the exact fitted NPZ grids from Git-tracked chunks.

    python scripts/restore_grids.py

Checks each grid's SHA-256, and, against assets/MANIFEST.json, that its dates and the summary.json it belongs to are
the ones in the repository now. A refit without `pack_grids.py` therefore fails here instead of pairing a new summary
with old grids.
"""
import json
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'assets/MANIFEST.json').read_text())
summary_path = root / manifest['summary']
if sha256(summary_path.read_bytes()).hexdigest() != manifest['summary_sha256']:
    raise SystemExit(f'{manifest["summary"]} changed since the grids were packed: run scripts/pack_grids.py after refitting')
summary = json.loads(summary_path.read_text())
for line in (root / 'assets/SHA256SUMS').read_text().splitlines():
    expected, name = line.split()
    target = root / name
    chunks = sorted((root / 'assets').glob(target.name + '.part*'))
    payload = b''.join(part.read_bytes() for part in chunks)
    if sha256(payload).hexdigest() != expected:
        raise ValueError(f'Checksum mismatch for {name}')
    track = target.stem
    if manifest['tracks'][track]['dates'] != summary[track]['dates']:
        raise SystemExit(f'{track}: packed grid dates differ from {manifest["summary"]}')
    target.write_bytes(payload)
print(f'restored {len(manifest["tracks"])} grids matching {manifest["summary"]}')

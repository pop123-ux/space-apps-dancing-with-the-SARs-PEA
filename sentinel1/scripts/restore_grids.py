# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Reassemble and verify the exact fitted NPZ grids from Git-tracked chunks, for every packed analysis window.

    python scripts/restore_grids.py

For each assets*/MANIFEST.json (assets/ for analysis/, assets_jan_oct/ for analysis_jan_oct/, ...): checks each grid's
SHA-256, and that its dates and the summary.json it belongs to are the ones in the repository now. A refit without
`pack_grids.py` therefore fails here instead of pairing a new summary with old grids.
"""
import json
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifests = sorted(root.glob('assets*/MANIFEST.json'))
if not manifests:
    raise SystemExit('no assets*/MANIFEST.json found: run scripts/pack_grids.py')
for mpath in manifests:
    assets = mpath.parent
    manifest = json.loads(mpath.read_text())
    summary_path = root / manifest['summary']
    if sha256(summary_path.read_bytes()).hexdigest() != manifest['summary_sha256']:
        raise SystemExit(f'{manifest["summary"]} changed since the grids were packed: run scripts/pack_grids.py after refitting '
                         '(on Windows, also check that git did not convert its line endings)')
    summary = json.loads(summary_path.read_text())
    for line in (assets / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split()
        target = root / name
        chunks = sorted(assets.glob(target.name + '.part*'))
        payload = b''.join(part.read_bytes() for part in chunks)
        if sha256(payload).hexdigest() != expected:
            raise ValueError(f'Checksum mismatch for {name}')
        track = target.stem
        if manifest['tracks'][track]['dates'] != summary[track]['dates']:
            raise SystemExit(f'{track}: packed grid dates differ from {manifest["summary"]}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    print(f'restored {len(manifest["tracks"])} grids matching {manifest["summary"]}')

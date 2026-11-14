# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Split the fitted NPZ grids into Git-sized chunks and write a manifest that ties them to summary.json.

    python scripts/pack_grids.py [ANALYSIS_DIRECTORY]     (default: analysis)

Run it after every refit, in the same commit as the new summary.json. It rewrites assets/<track>.npz.partNN,
assets/SHA256SUMS and assets/MANIFEST.json (the dates of each grid and the SHA-256 of the summary.json they belong
to). restore_grids.py refuses to restore grids whose dates or summary do not match.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

CHUNK = 600_000
root = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('analysis', nargs='?', default='analysis')
    analysis = root / ap.parse_args().analysis
    summary = json.loads((analysis / 'summary.json').read_text())
    assets = root / 'assets'
    assets.mkdir(exist_ok=True)
    sums, manifest = [], {'summary': str((analysis / 'summary.json').relative_to(root)),
                          'summary_sha256': hashlib.sha256((analysis / 'summary.json').read_bytes()).hexdigest(),
                          'tracks': {}}
    for track in summary:
        npz = analysis / f'{track}.npz'
        payload = npz.read_bytes()
        dates = [str(d) for d in np.load(npz)['dates']]
        if dates != summary[track]['dates']:
            raise SystemExit(f'{track}: grid dates differ from summary.json; refit before packing')
        for old in assets.glob(f'{track}.npz.part*'):
            old.unlink()
        for k in range(0, len(payload), CHUNK):
            (assets / f'{track}.npz.part{k // CHUNK:02d}').write_bytes(payload[k:k + CHUNK])
        digest = hashlib.sha256(payload).hexdigest()
        sums.append(f'{digest}  {npz.relative_to(root)}')
        manifest['tracks'][track] = {'npz': str(npz.relative_to(root)), 'sha256': digest, 'dates': dates}
    (assets / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    (assets / 'MANIFEST.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(f'packed {", ".join(manifest["tracks"])} for {manifest["summary"]}')


if __name__ == '__main__':
    main()

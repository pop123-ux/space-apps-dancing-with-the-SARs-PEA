# Owner: 03 · InSAR analyst (Alexandru, Eric)
"""Download the HyP3 products listed in provenance/hyp3_jobs_jan_nov.csv, without credentials, for fit.py.

    python scripts/fetch_jobs.py RAW_DIRECTORY [--keep-full] [--workers 8]

For each row with a URL: download the ZIP (HyP3 links are public until they expire, 29 Nov 2026 for these jobs),
check it opens and that its size matches the job record, record its SHA-256, then keep only the seven rasters fit.py
reads (unw_phase, corr, conncomp, water_mask, dem, lv_theta, lv_phi) in RAW_DIRECTORY/<job name>.zip. Slimming keeps the
whole 214-product stack on a small disk; the rasters are copied byte for byte. Writes RAW_DIRECTORY/SHA256SUMS for the
full archives as downloaded. Rows without a URL (jobs not finished when the list was written) stop the run.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

KEEP = ('unw_phase', 'corr', 'conncomp', 'water_mask', 'dem', 'lv_theta', 'lv_phi')
root = Path(__file__).resolve().parents[1]


def fetch(row, target, keep_full):
    out = target / (row['name'] + '.zip')
    temp = target / (row['name'] + '.download')
    for attempt in range(4):
        try:
            with urlopen(row['url'], timeout=180) as r, temp.open('wb') as f:
                shutil.copyfileobj(r, f, 1 << 20)
            break
        except OSError:
            if attempt == 3:
                raise
    size_kb = round(temp.stat().st_size / 1000)
    if row['size_kb'] and abs(size_kb - int(row['size_kb'])) > 1:
        raise SystemExit(f"{row['name']}: {size_kb} kB downloaded, the job record says {row['size_kb']} kB")
    with temp.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    with zipfile.ZipFile(temp) as src:
        names = src.namelist()
        if keep_full:
            temp.replace(out)
        else:
            with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as dst:
                for key in KEEP:
                    name = next(n for n in names if n.endswith('_' + key + '.tif'))
                    dst.writestr(name, src.read(name))
    temp.unlink(missing_ok=True)
    return f"{digest}  {row['filename']}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('raw', type=Path)
    ap.add_argument('--jobs', type=Path, default=root / 'provenance' / 'hyp3_jobs_jan_nov.csv')
    ap.add_argument('--keep-full', action='store_true')
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    rows = list(csv.DictReader(a.jobs.open(encoding='utf-8')))
    missing = [r['name'] for r in rows if not r['url']]
    if missing:
        raise SystemExit(f'{len(missing)} jobs have no download link yet, e.g. {missing[0]}')
    a.raw.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as pool:
        sums = list(pool.map(lambda r: fetch(r, a.raw, a.keep_full), rows))
    (a.raw / 'SHA256SUMS').write_text('\n'.join(sorted(sums, key=lambda s: s.split()[1])) + '\n')
    print(f'{len(rows)} products downloaded and checked into {a.raw}')


if __name__ == '__main__':
    main()

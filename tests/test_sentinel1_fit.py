# Owner: shared · announce changes; 01 reviews
"""Sentinel-1 fit maths: the solver and rate estimators in sentinel1/scripts/fit.py (no data needed).

1. One connected network gives the original single-network answer (a known truth comes back).
2. A chain with a gap (like NISAR 129A, no pair from 18 Jan to 23 Jun 2026) still solves every pixel, one zero per group.
3. The OLS rate with one offset per group and the within-group Theil-Sen rate recover the true rate across the gap.
"""
import importlib.util
import pathlib

import pytest

np = pytest.importorskip("numpy")
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("s1fit", ROOT / "sentinel1/scripts/fit.py")
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)


def test_one_group_recovers_truth():
    rng = np.random.default_rng(7)
    n = 16
    edges = [(i, i + 1) for i in range(n - 1)] + [(i, i + 2) for i in range(n - 2)]
    truth = np.cumsum(rng.normal(0, 2, (n, 5, 5)), axis=0)
    truth -= truth[0]
    data = np.stack([truth[j] - truth[i] for i, j in edges]).astype(np.float32)
    y = fit.solve(edges, n, data, np.ones_like(data))
    assert fit.date_groups(edges, n).max() == 0
    assert np.allclose(y, truth, atol=1e-3)


def test_gap_keeps_every_pixel():
    n = 15
    edges = [(i, i + 1) for i in range(n - 1) if i != 4]
    truth = np.cumsum(np.random.default_rng(3).normal(0, 1, (n, 4, 4)), axis=0)
    data = np.stack([truth[j] - truth[i] for i, j in edges]).astype(np.float32)
    groups = fit.date_groups(edges, n)
    y = fit.solve(edges, n, data, np.ones_like(data), groups)
    assert groups.tolist() == [0] * 5 + [1] * 10
    assert np.isfinite(y).all()
    assert np.allclose(y[0], 0) and np.allclose(y[5], 0)          # one zero date per group
    assert np.allclose(y[6:] - y[5], truth[6:] - truth[5], atol=1e-4)


def test_rates_across_a_gap():
    t = np.arange(15) / 30.0
    groups = np.array([0] * 5 + [1] * 10)
    y = 12.0 * t + np.where(groups == 1, 50.0, 0.0)                # arbitrary offset in the second group
    s = fit.stats(t, y, groups)
    assert abs(s["linear_mm_yr"] - 12.0) < 1e-9
    assert abs(s["theil_sen_mm_yr"] - 12.0) < 1e-9
    assert s["groups"] == groups.tolist()

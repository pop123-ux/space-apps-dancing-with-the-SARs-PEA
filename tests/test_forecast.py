# Owner: shared · announce changes; 01 reviews
"""Zone 4 forecast maths in sentinel1/scripts/forecast.py (no data needed).

1. The long-term model is a fixed line: rate (mm/yr) x days / 365.25 from the last radar estimate.
2. Persistence stays at zero change, and adding the long-term model leaves the other three paths unchanged.
3. 05's rain model with rain uncorrelated to the residual gives beta near zero and falls back to the Theil-Sen trend.
"""
import importlib.util
import pathlib
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sentinel1/scripts"))
spec = importlib.util.spec_from_file_location("s1forecast", ROOT / "sentinel1/scripts/forecast.py")
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)


def series():
    t = np.arange(-90, 1, 6, dtype=float)
    return t, -0.08 * t + np.sin(t / 9.0)


def test_long_term_is_a_fixed_rate():
    t, y = series()
    ahead = [6, 30, 88]
    out = fc.forecasts(t, y, ahead, long_term_rate=-5.48)
    assert np.allclose(out["long_term"], -5.48 * np.array(ahead) / 365.25)
    assert np.allclose(out["persistence"], 0)


def test_long_term_leaves_other_models_unchanged():
    t, y = series()
    a = fc.forecasts(t, y, [30, 88])
    b = fc.forecasts(t, y, [30, 88], long_term_rate=-5.48)
    for k in ("persistence", "theil_sen", "gaussian_process"):
        assert np.allclose(a[k], b[k])


def test_rain_model_without_signal_is_the_trend():
    t = np.arange(-90, 1, 6, dtype=float)
    y = -0.05 * t
    rain = np.tile([0.0, 10.0], len(t))[: len(t)]
    iss, cond, beta = fc.rain_model(t, y - y[-1], rain, rain[-1], [5.0], [30])
    assert abs(beta) < 1e-6
    assert np.allclose(iss, -0.05 * 30) and np.allclose(cond, -0.05 * 30)

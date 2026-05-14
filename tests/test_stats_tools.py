"""Unit tests for sim/stats_tools.py."""

import math
import pytest
from sim.stats_tools import (
    chi_square_test,
    ks_test_uniform,
    confidence_interval_95,
    min_replications,
    welch_ttest,
)


# ── chi_square_test ────────────────────────────────────────────────────────

def test_chi_square_perfect_fit():
    """Perfect uniform distribution should give χ²=0."""
    n = 1000
    k = 5
    obs = [n // k] * k
    probs = [1.0 / k] * k
    chi2, crit, reject = chi_square_test(obs, probs, n)
    assert chi2 == pytest.approx(0.0, abs=1e-9)
    assert not reject


def test_chi_square_obvious_reject():
    """All observations in one bin must reject H0."""
    n = 1000
    obs = [n, 0, 0, 0, 0]
    probs = [0.2] * 5
    _, _, reject = chi_square_test(obs, probs, n)
    assert reject


def test_chi_square_returns_three_values():
    obs = [50, 50]
    probs = [0.5, 0.5]
    result = chi_square_test(obs, probs, 100)
    assert len(result) == 3


# ── ks_test_uniform ────────────────────────────────────────────────────────

def test_ks_perfect_uniform():
    """Perfectly spaced [0,1) samples minimise D_n."""
    n = 1000
    samples = [i / n for i in range(n)]
    d, crit, reject = ks_test_uniform(samples)
    assert not reject


def test_ks_all_zeros_rejects():
    """Samples all equal to 0 should be far from U(0,1)."""
    samples = [0.0] * 500
    _, _, reject = ks_test_uniform(samples)
    assert reject


def test_ks_returns_three_values():
    result = ks_test_uniform([0.1, 0.5, 0.9])
    assert len(result) == 3


# ── confidence_interval_95 ─────────────────────────────────────────────────

def test_ci_mean_is_sample_mean():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, half, (lo, hi) = confidence_interval_95(data)
    assert mean == pytest.approx(3.0)
    assert lo == pytest.approx(mean - half)
    assert hi == pytest.approx(mean + half)


def test_ci_interval_contains_mean():
    data = list(range(1, 21))   # 1..20, mean=10.5
    mean, half, (lo, hi) = confidence_interval_95(data)
    assert lo < mean < hi


def test_ci_half_width_positive():
    data = [10.0, 12.0, 11.0, 9.0, 13.0]
    _, half, _ = confidence_interval_95(data)
    assert half > 0


def test_ci_single_element_no_crash():
    mean, half, (lo, hi) = confidence_interval_95([42.0])
    assert mean == 42.0
    assert half == 0.0


# ── min_replications ───────────────────────────────────────────────────────

def test_min_reps_returns_positive_int():
    data = [10.0, 12.0, 9.0, 11.0, 13.0]
    n = min_replications(data)
    assert isinstance(n, int)
    assert n >= 1


def test_min_reps_lower_error_requires_more():
    data = [10.0, 12.0, 9.0, 11.0, 13.0] * 5
    n_strict = min_replications(data, rel_error=0.01)
    n_loose  = min_replications(data, rel_error=0.10)
    assert n_strict >= n_loose


def test_min_reps_constant_data():
    """Constant data has std=0 → n_min = ceil((t·0/ε)²) = 0, clamped to n."""
    data = [5.0] * 10
    n = min_replications(data)
    assert n >= 0


# ── welch_ttest ────────────────────────────────────────────────────────────

def test_welch_identical_groups_no_reject():
    a = [10.0, 11.0, 10.5, 9.5, 10.2]
    b = [10.0, 11.0, 10.5, 9.5, 10.2]
    t, df, crit, decision = welch_ttest(a, b)
    assert t == pytest.approx(0.0, abs=1e-9)
    assert decision == "No rechazar H0"


def test_welch_very_different_groups_reject():
    a = [1.0, 1.1, 0.9, 1.0, 1.0] * 4
    b = [100.0, 101.0, 99.0, 100.5, 100.2] * 4
    t, df, crit, decision = welch_ttest(a, b)
    assert abs(t) > crit
    assert decision == "Rechazar H0"


def test_welch_returns_four_values():
    result = welch_ttest([1, 2, 3], [4, 5, 6])
    assert len(result) == 4


def test_welch_df_positive():
    t, df, crit, _ = welch_ttest([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert df > 0
    assert crit > 0

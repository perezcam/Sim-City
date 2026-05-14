"""Statistical tools implemented without scipy.

Provides:
  chi_square_test       — goodness-of-fit for discrete distributions
  ks_test_uniform       — Kolmogorov-Smirnov vs U(0,1)
  confidence_interval_95 — t-Student 95% CI for a sample
  min_replications      — minimum replicas for a target relative error
  welch_ttest           — two-sample Welch t-test
"""

from __future__ import annotations
import math


# ── Chi-square critical values at α = 0.05 (df 1..20) ────────────────────
# Source: standard statistical tables
_CHI2_CRIT_05 = {
    1: 3.841, 2: 5.991, 3: 7.815, 4: 9.488, 5: 11.070,
    6: 12.592, 7: 14.067, 8: 15.507, 9: 16.919, 10: 18.307,
    11: 19.675, 12: 21.026, 13: 22.362, 14: 23.685, 15: 24.996,
    16: 26.296, 17: 27.587, 18: 28.869, 19: 30.144, 20: 31.410,
}

# ── t critical values at α/2 = 0.025 (df 1..60, then inf) ────────────────
_T_CRIT_025 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447,  7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    25: 2.060, 30: 2.042, 40: 2.021, 50: 2.009, 60: 2.000,
}


def _t_critical(df: int) -> float:
    """Return t critical value for df degrees of freedom (α=0.05, two-tail)."""
    if df <= 0:
        return 12.706
    if df in _T_CRIT_025:
        return _T_CRIT_025[df]
    # Linear interpolation for df between table entries, else use z≈1.96
    keys = sorted(_T_CRIT_025)
    for i in range(len(keys) - 1):
        lo, hi = keys[i], keys[i + 1]
        if lo < df < hi:
            t_lo, t_hi = _T_CRIT_025[lo], _T_CRIT_025[hi]
            return t_lo + (t_hi - t_lo) * (df - lo) / (hi - lo)
    return 1.96   # large df → normal approximation


# ── Chi-square goodness-of-fit ─────────────────────────────────────────────

def chi_square_test(
    observed: list[int],
    expected_probs: list[float],
    n: int,
) -> tuple[float, float, bool]:
    """Chi-square goodness-of-fit test.

    Parameters
    ----------
    observed       : list of observed counts per category
    expected_probs : theoretical probabilities (must sum to ~1)
    n              : total number of observations (= sum(observed))

    Returns
    -------
    (chi2_stat, critical_value_05, reject_h0)
    reject_h0 is True when we reject at α = 0.05 (bad fit).
    """
    k = len(observed)
    chi2 = sum(
        (o - n * p) ** 2 / (n * p)
        for o, p in zip(observed, expected_probs)
        if n * p > 0
    )
    df = k - 1
    crit = _CHI2_CRIT_05.get(df, _CHI2_CRIT_05[max(_CHI2_CRIT_05)])
    return chi2, crit, chi2 > crit


# ── Kolmogorov-Smirnov vs U(0,1) ──────────────────────────────────────────

def ks_test_uniform(samples: list[float]) -> tuple[float, float, bool]:
    """One-sample KS test against U(0,1).

    Returns
    -------
    (D_n, critical_value_05, reject_h0)
    reject_h0 is True when we reject at α = 0.05.
    """
    n = len(samples)
    sorted_s = sorted(samples)
    d_max = 0.0
    for i, x in enumerate(sorted_s):
        f_empirical_hi = (i + 1) / n
        f_empirical_lo = i / n
        d_max = max(d_max, abs(f_empirical_hi - x), abs(f_empirical_lo - x))
    critical = 1.36 / math.sqrt(n)
    return d_max, critical, d_max > critical


# ── 95% Confidence interval (t-Student) ───────────────────────────────────

def confidence_interval_95(
    data: list[float],
) -> tuple[float, float, tuple[float, float]]:
    """95% confidence interval for the mean using t-Student.

    Returns
    -------
    (mean, half_width, (lower, upper))
    """
    n = len(data)
    if n < 2:
        m = data[0] if data else 0.0
        return m, 0.0, (m, m)
    mean = sum(data) / n
    var  = sum((x - mean) ** 2 for x in data) / (n - 1)
    std  = math.sqrt(var)
    t    = _t_critical(n - 1)
    half = t * std / math.sqrt(n)
    return mean, half, (mean - half, mean + half)


# ── Minimum replications ──────────────────────────────────────────────────

def min_replications(
    data: list[float],
    rel_error: float = 0.05,
    alpha: float = 0.05,
) -> int:
    """Minimum replications for a target relative half-width.

    n_min = ceil( (t_{α/2} · s / ε)² )  where ε = rel_error · |x̄|
    Uses the current n−1 degrees of freedom as approximation.
    """
    n = len(data)
    if n < 2:
        return n
    mean = sum(data) / n
    if mean == 0:
        return n
    var  = sum((x - mean) ** 2 for x in data) / (n - 1)
    std  = math.sqrt(var)
    t    = _t_critical(n - 1)
    eps  = rel_error * abs(mean)
    if eps == 0:
        return n
    n_min = math.ceil((t * std / eps) ** 2)
    return n_min


# ── Welch two-sample t-test ───────────────────────────────────────────────

def welch_ttest(
    a: list[float],
    b: list[float],
) -> tuple[float, int, float, str]:
    """Welch's t-test for independent samples with unequal variances.

    Returns
    -------
    (t_stat, df_welch, critical_value_05, decision)
    decision is 'Rechazar H0' or 'No rechazar H0'.
    """
    na, nb = len(a), len(b)
    mean_a = sum(a) / na
    mean_b = sum(b) / nb
    var_a  = sum((x - mean_a) ** 2 for x in a) / (na - 1) if na > 1 else 0.0
    var_b  = sum((x - mean_b) ** 2 for x in b) / (nb - 1) if nb > 1 else 0.0

    se = math.sqrt(var_a / na + var_b / nb)
    if se == 0:
        return 0.0, na + nb - 2, 0.0, "No rechazar H0"

    t_stat = (mean_a - mean_b) / se

    # Welch-Satterthwaite degrees of freedom
    num = (var_a / na + var_b / nb) ** 2
    den = (var_a / na) ** 2 / (na - 1) + (var_b / nb) ** 2 / (nb - 1)
    df  = int(num / den) if den > 0 else na + nb - 2

    crit     = _t_critical(df)
    decision = "Rechazar H0" if abs(t_stat) > crit else "No rechazar H0"
    return t_stat, df, crit, decision

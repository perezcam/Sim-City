"""Statistical validation of the LCG generator.

Each test uses α = 0.05. We expect *not* to reject H0 for a correct generator.
"""

import math
import pytest
from sim.random_vars import seed, uniform, exponential, sample_cdf
from sim.stats_tools import chi_square_test, ks_test_uniform
from sim import tables


# ── Uniform distribution tests ─────────────────────────────────────────────

def test_uniform_chi_square():
    """Chi-square with 10 equal bins on N=10 000 samples."""
    seed(1)
    n     = 10_000
    k     = 10
    bins  = [0] * k
    for _ in range(n):
        v = uniform()
        bins[int(v * k)] += 1
    expected = [1.0 / k] * k
    _, crit, reject = chi_square_test(bins, expected, n)
    assert not reject, f"Uniform chi-square rejected H0 (should not at α=0.05)"


def test_uniform_ks():
    """Kolmogorov-Smirnov test of U(0,1) on N=5 000 samples."""
    seed(2)
    samples = [uniform() for _ in range(5_000)]
    d_n, crit, reject = ks_test_uniform(samples)
    assert not reject, f"Uniform KS rejected H0: D={d_n:.4f} > {crit:.4f}"


# ── Exponential distribution test ─────────────────────────────────────────

def test_exponential_ks():
    """Transform Exp(mean) samples to U(0,1) via CDF and run KS."""
    seed(10)
    mean    = 10.0
    n       = 5_000
    samples = [exponential(mean) for _ in range(n)]
    # CDF of Exp(mean): F(x) = 1 - exp(-x/mean)
    uniform_samples = [1.0 - math.exp(-x / mean) for x in samples]
    d_n, crit, reject = ks_test_uniform(uniform_samples)
    assert not reject, f"Exponential KS rejected H0: D={d_n:.4f} > {crit:.4f}"


# ── Discrete distributions (birth count and desired children) ─────────────

def test_birth_count_chi_square():
    """Chi-square on 2 000 samples of birth_count_cdf."""
    seed(4)
    values, cdf = tables.birth_count_cdf()
    probs = [cdf[0]] + [cdf[i] - cdf[i - 1] for i in range(1, len(cdf))]
    n    = 2_000
    obs  = [0] * len(values)
    for _ in range(n):
        v = sample_cdf(values, cdf)
        obs[values.index(v)] += 1
    _, crit, reject = chi_square_test(obs, probs, n)
    assert not reject, f"birth_count chi-square rejected H0"


def test_desired_children_chi_square():
    """Chi-square on 2 000 samples of desired_children_cdf."""
    seed(20)
    values, cdf = tables.desired_children_cdf()
    probs = [cdf[0]] + [cdf[i] - cdf[i - 1] for i in range(1, len(cdf))]
    n    = 2_000
    obs  = [0] * len(values)
    for _ in range(n):
        v = sample_cdf(values, cdf)
        obs[values.index(v)] += 1
    _, crit, reject = chi_square_test(obs, probs, n)
    assert not reject, f"desired_children chi-square rejected H0"

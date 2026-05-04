"""Tests for sim/random_vars.py."""

import random
import pytest
from sim import random_vars


def test_uniform_range():
    random.seed(0)
    for _ in range(1000):
        v = random_vars.uniform()
        assert 0.0 <= v < 1.0


def test_bernoulli_always_true_when_p1():
    random.seed(0)
    assert all(random_vars.bernoulli(1.0) for _ in range(100))


def test_bernoulli_always_false_when_p0():
    random.seed(0)
    assert not any(random_vars.bernoulli(0.0) for _ in range(100))


def test_bernoulli_approx_frequency():
    random.seed(42)
    n = 10_000
    hits = sum(random_vars.bernoulli(0.3) for _ in range(n))
    assert abs(hits / n - 0.3) < 0.02


def test_exponential_positive():
    random.seed(0)
    for _ in range(500):
        assert random_vars.exponential(6) > 0


def test_random_sex_balance():
    random.seed(7)
    sexes = [random_vars.random_sex() for _ in range(10_000)]
    ratio = sexes.count("M") / len(sexes)
    assert 0.48 <= ratio <= 0.52


def test_random_age_initial_months_range():
    random.seed(0)
    for _ in range(1000):
        age = random_vars.random_age_initial_months()
        assert 0 <= age < 100 * 12


def test_sample_cdf_returns_valid_value():
    random.seed(0)
    values = [1, 2, 3]
    cdf    = [0.2, 0.7, 1.0]
    for _ in range(500):
        v = random_vars.sample_cdf(values, cdf)
        assert v in values

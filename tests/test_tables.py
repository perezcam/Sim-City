"""Tests for sim/tables.py."""

import pytest
from sim import tables


# ── death_prob_annual ──────────────────────────────────────────────────────

@pytest.mark.parametrize("age,sex", [
    (5,   "M"), (5,   "F"),
    (20,  "M"), (20,  "F"),
    (60,  "M"), (60,  "F"),
    (100, "M"), (100, "F"),
])
def test_death_prob_annual_range(age, sex):
    p = tables.death_prob_annual(age, sex)
    assert 0.0 <= p <= 1.0, f"death_prob_annual({age}, {sex}) = {p} fuera de [0,1]"


def test_death_prob_monthly_less_than_annual():
    for age in [5, 20, 60, 100]:
        for sex in ("M", "F"):
            p_annual = tables.death_prob_annual(age, sex)
            p_monthly = tables.death_prob_monthly(age, sex)
            assert p_monthly < p_annual, (
                f"death_prob_monthly debe ser < annual para age={age} sex={sex}"
            )


def test_death_prob_monthly_compounds_to_annual():
    """12 meses de prob mensual deben aproximar la prob anual."""
    for age in [5, 20, 60, 100]:
        for sex in ("M", "F"):
            p_annual = tables.death_prob_annual(age, sex)
            p_monthly = tables.death_prob_monthly(age, sex)
            p_reconstructed = 1 - (1 - p_monthly) ** 12
            assert abs(p_reconstructed - p_annual) < 1e-9


# ── pregnancy_prob ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("age", [5, 13, 18, 25, 40, 50, 70])
def test_pregnancy_prob_range(age):
    p = tables.pregnancy_prob(age)
    assert 0.0 <= p <= 1.0

def test_pregnancy_prob_under_12_is_zero():
    assert tables.pregnancy_prob(11) == 0.0
    assert tables.pregnancy_prob(0) == 0.0


# ── want_partner_prob ──────────────────────────────────────────────────────

@pytest.mark.parametrize("age", [13, 18, 25, 40, 55, 80])
def test_want_partner_prob_range(age):
    p = tables.want_partner_prob(age)
    assert 0.0 <= p <= 1.0

def test_want_partner_prob_under_12_is_zero():
    assert tables.want_partner_prob(10) == 0.0


# ── partner_formation_prob ────────────────────────────────────────────────

@pytest.mark.parametrize("diff", [0, 3, 7, 12, 17, 25])
def test_partner_formation_prob_range(diff):
    p = tables.partner_formation_prob(diff)
    assert 0.0 <= p <= 1.0


# ── desired_children_cdf ──────────────────────────────────────────────────

def test_desired_children_cdf_sums_to_one():
    values, cdf = tables.desired_children_cdf()
    assert abs(cdf[-1] - 1.0) < 1e-9
    assert len(values) == len(cdf)

def test_desired_children_cdf_monotone():
    _, cdf = tables.desired_children_cdf()
    for i in range(1, len(cdf)):
        assert cdf[i] >= cdf[i - 1]


# ── birth_count_cdf ────────────────────────────────────────────────────────

def test_birth_count_cdf_sums_to_one():
    values, cdf = tables.birth_count_cdf()
    assert abs(cdf[-1] - 1.0) < 1e-9
    assert len(values) == len(cdf)

def test_birth_count_cdf_monotone():
    _, cdf = tables.birth_count_cdf()
    for i in range(1, len(cdf)):
        assert cdf[i] >= cdf[i - 1]


# ── PREGNANCY_DURATION_MONTHS ──────────────────────────────────────────────

def test_pregnancy_duration_constant_exists():
    assert tables.PREGNANCY_DURATION_MONTHS == 9

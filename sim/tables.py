"""Probability lookup tables from the problem statement."""

import math

# ── Death probabilities (annual) by age range and sex ──────────────────────
_DEATH_MALE = [
    (12,   0.25),
    (45,   0.10),
    (76,   0.30),
    (125,  0.70),
]
_DEATH_FEMALE = [
    (12,   0.25),
    (45,   0.15),
    (76,   0.35),
    (125,  0.65),
]

def _lookup(table: list, age: float) -> float:
    for upper, prob in table:
        if age < upper:
            return prob
    return table[-1][1]


def death_prob_annual(age: float, sex: str) -> float:
    """Annual probability of dying given age (years) and sex ('M'/'F')."""
    table = _DEATH_MALE if sex == "M" else _DEATH_FEMALE
    return _lookup(table, age)


def death_prob_monthly(age: float, sex: str) -> float:
    """Convert annual death probability to monthly equivalent."""
    p_annual = death_prob_annual(age, sex)
    return 1.0 - (1.0 - p_annual) ** (1.0 / 12.0)


# ── Pregnancy probability (monthly, applied to women with partner) ──────────
_PREGNANCY = [
    (15,  0.20),
    (21,  0.45),
    (35,  0.80),
    (45,  0.40),
    (60,  0.20),
    (125, 0.05),
]

def pregnancy_prob(age: float) -> float:
    """Monthly probability of pregnancy given woman's age (years)."""
    if age < 12:
        return 0.0
    return _lookup(_PREGNANCY, age)


# ── Wanting a partner probability by age ───────────────────────────────────
_WANT_PARTNER = [
    (15,  0.60),
    (21,  0.65),
    (35,  0.80),
    (45,  0.60),
    (60,  0.50),
    (125, 0.20),
]

def want_partner_prob(age: float) -> float:
    """Probability that a person aged `age` wants a partner."""
    if age < 12:
        return 0.0
    return _lookup(_WANT_PARTNER, age)


# ── Partner formation probability by age difference ───────────────────────
_PARTNER_FORM = [
    (5,   0.45),
    (10,  0.40),
    (15,  0.35),
    (20,  0.25),
    (200, 0.15),
]

def partner_formation_prob(age_diff: float) -> float:
    """Probability of forming a couple given absolute age difference (years)."""
    return _lookup(_PARTNER_FORM, age_diff)


# ── Breakup monthly probability (converted from 0.2 annual) ────────────────
BREAKUP_PROB_MONTHLY = 1.0 - (1.0 - 0.2) ** (1.0 / 12.0)


# ── Solitude duration (mean months) by age after breakup/widowhood ─────────
# λ given in problem as mean time; exponential param = 1/mean
_SOLITUDE_MEAN_MONTHS = [
    (15,  3.0),
    (21,  6.0),
    (35,  6.0),
    (45,  12.0),
    (60,  24.0),
    (125, 48.0),
]

def solitude_mean_months(age: float) -> float:
    """Mean solitude duration in months after breakup/widowhood."""
    if age < 12:
        return 1.0
    return _lookup(_SOLITUDE_MEAN_MONTHS, age)


# ── Desired children distribution ──────────────────────────────────────────
# Raw weights from table: 1→0.6, 2→0.75, 3→0.35, 4→0.2, 5→0.1, 6+→0.05
_DESIRED_CHILDREN_VALUES  = [1, 2, 3, 4, 5, 6]
_DESIRED_CHILDREN_WEIGHTS = [0.6, 0.75, 0.35, 0.2, 0.1, 0.05]
_DESIRED_CHILDREN_TOTAL   = sum(_DESIRED_CHILDREN_WEIGHTS)
_DESIRED_CHILDREN_CDF     = []
_cumsum = 0.0
for _w in _DESIRED_CHILDREN_WEIGHTS:
    _cumsum += _w / _DESIRED_CHILDREN_TOTAL
    _DESIRED_CHILDREN_CDF.append(_cumsum)


def desired_children_cdf() -> tuple[list[int], list[float]]:
    """Return (values, cdf) for sampling desired children count."""
    return _DESIRED_CHILDREN_VALUES, _DESIRED_CHILDREN_CDF


# ── Multiple birth distribution ─────────────────────────────────────────────
_BIRTH_VALUES  = [1, 2, 3, 4, 5]
_BIRTH_WEIGHTS = [0.70, 0.18, 0.08, 0.04, 0.02]
_BIRTH_TOTAL   = sum(_BIRTH_WEIGHTS)
_BIRTH_CDF     = []
_cumsum = 0.0
for _w in _BIRTH_WEIGHTS:
    _cumsum += _w / _BIRTH_TOTAL
    _BIRTH_CDF.append(_cumsum)


def birth_count_cdf() -> tuple[list[int], list[float]]:
    """Return (values, cdf) for sampling number of babies born."""
    return _BIRTH_VALUES, _BIRTH_CDF

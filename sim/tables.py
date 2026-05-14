"""Probability lookup tables from the problem statement."""

# ── Death probabilities by age range and sex ───────────────────────────────
# Each entry: (age_lo, age_hi, p_male, p_female)
# p is the CUMULATIVE probability of dying at some point within the range,
# not a per-year rate.  E.g. 0.25 for 0-12 means 25% of children die before
# turning 12 (so 75% survive childhood).
_DEATH_RANGES = [
    (0,    12,  0.25, 0.25),
    (12,   45,  0.10, 0.15),
    (45,   76,  0.30, 0.35),
    (76,  125,  0.70, 0.65),
]


def _lookup(table: list, age: float) -> float:
    for upper, prob in table:
        if age < upper:
            return prob
    return table[-1][1]


def _death_prob_monthly_for_range(lo: int, hi: int, p_range: float) -> float:
    """Monthly hazard derived from a cumulative range probability."""
    duration_months = (hi - lo) * 12
    return 1.0 - (1.0 - p_range) ** (1.0 / duration_months)


def death_prob_monthly(age: float, sex: str) -> float:
    """Monthly probability of dying given age (years) and sex ('M'/'F')."""
    for lo, hi, pm, pf in _DEATH_RANGES:
        if age < hi:
            return _death_prob_monthly_for_range(lo, hi, pm if sex == "M" else pf)
    lo, hi, pm, pf = _DEATH_RANGES[-1]
    return _death_prob_monthly_for_range(lo, hi, pm if sex == "M" else pf)


def death_prob_annual(age: float, sex: str) -> float:
    """Annual probability of dying given age (years) and sex ('M'/'F')."""
    p_monthly = death_prob_monthly(age, sex)
    return 1.0 - (1.0 - p_monthly) ** 12


# ── Pregnancy probability ──────────────────────────────────────────────────
# Each entry: (age_lo, age_hi, p)
# p interpretation depends on `mode` passed to pregnancy_prob():
#   'monthly' — use p directly as monthly probability
#   'annual'  — p is an annual rate; convert with 1-(1-p)^(1/12)
#   'range'   — p is cumulative probability over the full age range;
#               convert with 1-(1-p)^(1/duration_months)
_PREGNANCY_RANGES = [
    (12,  15,  0.20),
    (15,  21,  0.45),
    (21,  35,  0.80),
    (35,  45,  0.40),
    (45,  60,  0.20),
    (60, 125,  0.05),
]


def pregnancy_prob(age: float, mode: str = "range") -> float:
    """Monthly probability of pregnancy given woman's age and interpretation mode."""
    if age < 12:
        return 0.0
    for lo, hi, p in _PREGNANCY_RANGES:
        if age < hi:
            return _pregnancy_monthly(lo, hi, p, mode)
    lo, hi, p = _PREGNANCY_RANGES[-1]
    return _pregnancy_monthly(lo, hi, p, mode)


def _pregnancy_monthly(lo: int, hi: int, p: float, mode: str) -> float:
    if mode == "monthly":
        return p
    if mode == "annual":
        return 1.0 - (1.0 - p) ** (1.0 / 12.0)
    # "range": cumulative probability over the range
    duration_months = (hi - lo) * 12
    return 1.0 - (1.0 - p) ** (1.0 / duration_months)


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


# ── Fixed constants ────────────────────────────────────────────────────────
PREGNANCY_DURATION_MONTHS = 9

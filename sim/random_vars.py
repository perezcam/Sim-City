"""Random variable generators. All randomness flows through this module.

Uses a home-grown Linear Congruential Generator (LCG) with Numerical Recipes
parameters: m=2^32, a=1664525, c=1013904223.
"""

import math


class LCG:
    """Linear Congruential Generator: x_{n+1} = (a*x_n + c) mod m."""

    _A = 1_664_525
    _C = 1_013_904_223
    _M = 0x1_0000_0000   # 2^32

    def __init__(self, initial_seed: int = 12345) -> None:
        self._state: int = initial_seed & 0xFFFF_FFFF

    def seed(self, s: int) -> None:
        self._state = s & 0xFFFF_FFFF

    def random(self) -> float:
        """Return next U(0,1) value."""
        self._state = (self._A * self._state + self._C) % self._M
        return self._state / self._M


# ── Module-level singleton ─────────────────────────────────────────────────
_lcg = LCG()


def seed(s: int) -> None:
    """Seed the module-level LCG."""
    _lcg.seed(s)


# ── Public random-variable functions ──────────────────────────────────────

def uniform() -> float:
    """U(0,1)."""
    return _lcg.random()


def bernoulli(p: float) -> bool:
    """True with probability p."""
    return _lcg.random() < p


def exponential(mean: float) -> float:
    """Sample from Exp(mean) via inverse-transform: -mean * ln(1 - U)."""
    u = _lcg.random()
    return -mean * math.log(1.0 - max(u, 1e-15))


def random_sex() -> str:
    """'M' or 'F' with equal probability."""
    return "M" if _lcg.random() < 0.5 else "F"


def random_age_initial_months() -> int:
    """Initial age in months: U(0,100) years converted to whole months."""
    return int(_lcg.random() * 100 * 12)


def sample_cdf(values: list, cdf: list):
    """Inverse-transform sampling from a discrete CDF."""
    u = _lcg.random()
    for v, c in zip(values, cdf):
        if u <= c:
            return v
    return values[-1]


def shuffle(lst: list) -> None:
    """In-place Fisher-Yates shuffle using the LCG."""
    n = len(lst)
    for i in range(n - 1, 0, -1):
        j = int(_lcg.random() * (i + 1))
        lst[i], lst[j] = lst[j], lst[i]

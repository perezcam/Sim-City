"""Random variable generators. All randomness flows through this module."""

import random
import math


def uniform() -> float:
    """U(0,1)."""
    return random.random()


def bernoulli(p: float) -> bool:
    """True with probability p."""
    return random.random() < p


def exponential(mean: float) -> float:
    """Sample from Exp(mean). Returns a value in the same unit as mean."""
    return random.expovariate(1.0 / mean)


def random_sex() -> str:
    """'M' or 'F' with equal probability."""
    return "M" if random.random() < 0.5 else "F"


def random_age_initial_months() -> int:
    """Initial age in months: U(0,100) years converted to whole months."""
    return int(random.uniform(0, 100) * 12)


def sample_cdf(values: list, cdf: list):
    """Inverse-transform sampling from a discrete CDF."""
    u = random.random()
    for v, c in zip(values, cdf):
        if u <= c:
            return v
    return values[-1]


def shuffle(lst: list) -> None:
    """In-place Fisher-Yates shuffle."""
    random.shuffle(lst)

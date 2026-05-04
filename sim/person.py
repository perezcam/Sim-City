"""Person entity."""

from __future__ import annotations
from sim import tables, random_vars


class Person:
    _next_id = 0

    def __init__(self, sex: str, age_months: int):
        Person._next_id += 1
        self.id: int = Person._next_id
        self.sex: str = sex                      # 'M' or 'F'
        self.age_months: int = age_months
        self.alive: bool = True

        self.couple_id: int | None = None
        self.children_count: int = 0
        self.children_desired: int = self._sample_desired_children()

        self.pregnant: bool = False
        self.pregnancy_months_remaining: int = 0

        # > 0 means person cannot seek a new partner yet
        self.solitude_months_remaining: int = 0

        # Parenthood (None for the founding generation)
        self.father_id: int | None = None
        self.mother_id: int | None = None
        self.birth_year: int = 0

    @staticmethod
    def _sample_desired_children() -> int:
        values, cdf = tables.desired_children_cdf()
        return random_vars.sample_cdf(values, cdf)

    # ── Derived properties ──────────────────────────────────────────────────

    @property
    def age_years(self) -> float:
        return self.age_months / 12.0

    @property
    def is_single(self) -> bool:
        return self.couple_id is None

    @property
    def is_available_for_partner(self) -> bool:
        return (
            self.alive
            and self.is_single
            and self.solitude_months_remaining <= 0
            and self.age_years >= 12
        )

    def enter_solitude(self) -> None:
        """Called after breakup or widowing."""
        mean = tables.solitude_mean_months(self.age_years)
        duration = int(round(random_vars.exponential(mean)))
        self.solitude_months_remaining = max(1, duration)
        self.couple_id = None
        self.pregnant = False
        self.pregnancy_months_remaining = 0

    def __repr__(self) -> str:
        status = "vivo" if self.alive else "muerto"
        pareja = f"pareja={self.couple_id}" if self.couple_id else "soltero"
        return (
            f"Person(id={self.id}, {self.sex}, "
            f"{self.age_years:.1f}a, {status}, {pareja}, "
            f"hijos={self.children_count}/{self.children_desired})"
        )

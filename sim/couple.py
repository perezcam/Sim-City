"""Couple entity."""

from __future__ import annotations


class Couple:
    _next_id = 0

    def __init__(self, person_a_id: int, person_b_id: int):
        Couple._next_id += 1
        self.id: int = Couple._next_id
        self.person_a_id: int = person_a_id
        self.person_b_id: int = person_b_id
        self.months_together: int = 0

    def other(self, person_id: int) -> int:
        """Return the partner's id given one member's id."""
        return self.person_b_id if person_id == self.person_a_id else self.person_a_id

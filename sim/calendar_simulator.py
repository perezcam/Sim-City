"""Event-calendar simulator using an explicit Future Event List (FEL)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from sim.simulator import Simulator


@dataclass(order=True)
class _Event:
    month: int
    priority: int
    seq: int
    kind: str = field(compare=False)


# Keep same causal order as the step simulator.
_PHASES = [
    (0, "age"),
    (1, "deaths"),
    (2, "breakups"),
    (3, "solitude"),
    (4, "partner_formation"),
    (5, "pregnancies"),
    (6, "births"),
    (7, "year_end"),
]


class CalendarSimulator(Simulator):
    """Simulator variant that executes the model through an event calendar.

    The model rules are intentionally the same as ``Simulator``; only the
    time-advance mechanism changes from a fixed loop to a future-event list.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue: list[_Event] = []
        self._seq: int = 0

    def run(self) -> list[dict]:
        self._bootstrap_calendar()
        while self._queue:
            ev = heapq.heappop(self._queue)
            if ev.month >= self.total_months:
                continue
            self.month = ev.month
            self._dispatch(ev.kind)
        return self.stats

    def _bootstrap_calendar(self) -> None:
        for month in range(self.total_months):
            for priority, kind in _PHASES:
                self._push(month, priority, kind)

    def _push(self, month: int, priority: int, kind: str) -> None:
        self._seq += 1
        heapq.heappush(self._queue, _Event(month, priority, self._seq, kind))

    def _dispatch(self, kind: str) -> None:
        if kind == "age":
            self._age_everyone()
            return
        if kind == "deaths":
            self._process_deaths()
            return
        if kind == "breakups":
            self._process_breakups()
            return
        if kind == "solitude":
            self._process_solitude()
            return
        if kind == "partner_formation":
            self._process_partner_formation()
            return
        if kind == "pregnancies":
            self._process_pregnancies()
            return
        if kind == "births":
            self._process_births()
            return
        if kind == "year_end":
            if (self.month + 1) % 12 == 0:
                self._record_stats()
                self._births_this_year = 0
                self._deaths_this_year = 0
                self._couples_formed_this_year = 0
                self._breakups_this_year = 0
            return
        raise ValueError(f"Unknown event kind: {kind}")

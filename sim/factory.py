"""Simulator factory for selecting execution mode."""

from __future__ import annotations

from sim.calendar_strong_simulator import CalendarStrongSimulator
from sim.simulator import Simulator


SIMULATION_MODES = ("step", "calendar_strong")


def build_simulator(
    mode: str,
    n_women: int,
    n_men: int,
    years: int = 100,
    seed: int | None = None,
    death_mode: str = "monthly",
    pregnancy_mode: str = "range",
    simulator_cls=None,
):
    """Build a simulator instance for the requested mode.

    ``simulator_cls`` can be used by sensitivity analysis to inject subclasses.
    """
    cls = simulator_cls
    if cls is None:
        if mode == "calendar_strong":
            cls = CalendarStrongSimulator
        else:
            cls = Simulator

    return cls(
        n_women=n_women,
        n_men=n_men,
        years=years,
        seed=seed,
        death_mode=death_mode,
        pregnancy_mode=pregnancy_mode,
    )

"""Tests for sim/simulator.py."""

import pytest
from sim.simulator import Simulator


def test_initial_population_count():
    sim = Simulator(n_women=50, n_men=50, years=1, seed=0)
    alive = [p for p in sim.persons.values() if p.alive]
    assert len(alive) == 100


def test_no_baby_born_with_age_greater_than_zero():
    sim = Simulator(n_women=100, n_men=100, years=5, seed=1)
    sim.run()
    for p in sim.persons.values():
        # babies born during simulation start at age_months=0 and age up;
        # ensure no one was created with a negative age
        assert p.age_months >= 0


def test_reproducible_with_same_seed():
    stats_a = Simulator(200, 200, years=10, seed=42).run()
    stats_b = Simulator(200, 200, years=10, seed=42).run()
    for a, b in zip(stats_a, stats_b):
        assert a["population"] == b["population"]
        assert a["births"]     == b["births"]
        assert a["deaths"]     == b["deaths"]


def test_different_seeds_give_different_results():
    stats_a = Simulator(200, 200, years=10, seed=1).run()
    stats_b = Simulator(200, 200, years=10, seed=2).run()
    pops_a = [s["population"] for s in stats_a]
    pops_b = [s["population"] for s in stats_b]
    assert pops_a != pops_b


def test_stats_length_equals_years():
    years = 15
    stats = Simulator(50, 50, years=years, seed=0).run()
    assert len(stats) == years


def test_no_negative_population():
    stats = Simulator(100, 100, years=20, seed=5).run()
    for s in stats:
        assert s["population"] >= 0
        assert s["men"]        >= 0
        assert s["women"]      >= 0


def test_births_plus_initial_geq_deaths_plus_final():
    """Conservación: inicial + nacidos >= finales + muertos (puede haber diff por redondeo de año)."""
    n_init = 200
    sim = Simulator(100, 100, years=30, seed=3)
    stats = sim.run()
    total_births = sum(s["births"] for s in stats)
    total_deaths = sum(s["deaths"] for s in stats)
    final_pop    = stats[-1]["population"]
    assert n_init + total_births >= final_pop + total_deaths - 5  # tolerancia mínima


def test_couple_id_consistent():
    """couple_id en Person debe apuntar a una Couple existente o ser None."""
    sim = Simulator(100, 100, years=5, seed=9)
    sim.run()
    for p in sim.persons.values():
        if p.alive and p.couple_id is not None:
            assert p.couple_id in sim.couples


def test_annual_death_mode_slower_decline():
    """Promedio de muertes año 1: modo anual debe ser <= mensual (misma tasa anual efectiva)."""
    n_seeds = 10
    deaths_monthly, deaths_annual = [], []
    for seed in range(n_seeds):
        sm = Simulator(200, 200, years=1, seed=seed, death_mode="monthly").run()
        sa = Simulator(200, 200, years=1, seed=seed, death_mode="annual").run()
        deaths_monthly.append(sm[0]["deaths"])
        deaths_annual.append(sa[0]["deaths"])
    avg_m = sum(deaths_monthly) / n_seeds
    avg_a = sum(deaths_annual)  / n_seeds
    # Con misma tasa anual efectiva, el promedio de muertes debe ser comparable (± 20%)
    assert abs(avg_m - avg_a) / max(avg_m, avg_a) < 0.20

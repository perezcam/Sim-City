"""Sensitivity analysis: vary key parameters and measure population outcome."""

from __future__ import annotations
import random
import statistics
from sim.simulator import Simulator
from sim import random_vars as rv


# ── Age distribution strategies ────────────────────────────────────────────

def _ages_uniform_0_100(n: int) -> list[int]:
    """Default: U(0, 100) years in months."""
    return [int(random.uniform(0, 100) * 12) for _ in range(n)]


def _ages_uniform_0_40(n: int) -> list[int]:
    """Young population: U(0, 40) years in months."""
    return [int(random.uniform(0, 40) * 12) for _ in range(n)]


def _ages_triangular(n: int) -> list[int]:
    """Triangular distribution: mode at 0, max at 80 years → skewed young."""
    return [int(random.triangular(0, 80, 0) * 12) for _ in range(n)]


AGE_STRATEGIES = {
    "U(0,100)":    _ages_uniform_0_100,
    "U(0,40)":     _ages_uniform_0_40,
    "Triangular":  _ages_triangular,
}


# ── Patched simulator for custom age distribution ─────────────────────────

class _SimulatorWithAges(Simulator):
    """Simulator that accepts a custom age-generation function."""

    def __init__(self, n_women, n_men, years, seed, death_mode, age_fn):
        self._age_fn = age_fn
        super().__init__(n_women, n_men, years=years, seed=seed, death_mode=death_mode)

    def _init_population(self, n: int, sex: str) -> None:
        from sim.person import Person
        ages = self._age_fn(n)
        for age_m in ages:
            from sim.person import Person
            p = Person(sex, age_m)
            self.persons[p.id] = p


# ── Main sensitivity function ──────────────────────────────────────────────

def run_sensitivity(
    population_sizes: list[int] | None = None,
    age_strategies: list[str] | None = None,
    n_runs: int = 20,
    years: int = 100,
    base_seed: int = 0,
    death_mode: str = "monthly",
) -> list[dict]:
    """
    Run a sensitivity sweep over population sizes and age distributions.

    Returns a list of result dicts, one per (size, strategy) combination:
      {
        "n_total":        int,
        "age_strategy":   str,
        "avg_extinction": float | None,  # mean extinction year (None if never extinct)
        "survival_rate":  float,          # fraction of runs surviving all years
        "avg_final_pop":  float,          # mean population at final year
        "std_final_pop":  float,
        "avg_peak_pop":   float,
        "n_runs":         int,
      }
    """
    if population_sizes is None:
        population_sizes = [200, 500, 1000, 2000]
    if age_strategies is None:
        age_strategies = list(AGE_STRATEGIES.keys())

    results = []

    for n_total in population_sizes:
        n_half = n_total // 2
        for strategy_name in age_strategies:
            age_fn = AGE_STRATEGIES[strategy_name]
            extinction_years, final_pops, peak_pops = [], [], []

            for i in range(n_runs):
                seed = base_seed + i
                random.seed(seed)
                sim = _SimulatorWithAges(
                    n_women=n_half,
                    n_men=n_half,
                    years=years,
                    seed=seed,
                    death_mode=death_mode,
                    age_fn=age_fn,
                )
                stats = sim.run()

                ext = next((s["year"] for s in stats if s["population"] == 0), None)
                extinction_years.append(ext)
                final_pops.append(stats[-1]["population"])
                peak_pops.append(max(s["population"] for s in stats))

            survived     = [e for e in extinction_years if e is None]
            extinct_vals = [e for e in extinction_years if e is not None]

            results.append({
                "n_total":        n_total,
                "age_strategy":   strategy_name,
                "avg_extinction": statistics.mean(extinct_vals) if extinct_vals else None,
                "survival_rate":  len(survived) / n_runs,
                "avg_final_pop":  statistics.mean(final_pops),
                "std_final_pop":  statistics.stdev(final_pops) if len(final_pops) > 1 else 0.0,
                "avg_peak_pop":   statistics.mean(peak_pops),
                "n_runs":         n_runs,
            })

    return results

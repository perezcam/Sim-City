"""Sensitivity analysis: vary key parameters and measure population outcome."""

from __future__ import annotations
import math
import statistics
from sim.simulator import Simulator
from sim.factory import build_simulator
from sim import random_vars as rv
from sim.stats_tools import confidence_interval_95, welch_ttest


# ── Age distribution strategies (all use the LCG) ─────────────────────────

def _ages_uniform_0_100(n: int) -> list[int]:
    """U(0, 100) years → months."""
    return [int(rv.uniform() * 100 * 12) for _ in range(n)]


def _ages_uniform_0_40(n: int) -> list[int]:
    """Young population: U(0, 40) years → months."""
    return [int(rv.uniform() * 40 * 12) for _ in range(n)]


def _ages_triangular(n: int) -> list[int]:
    """Triangular(low=0, high=80, mode=0) → skewed-young, in months.

    Inverse-CDF: with a=0, b=80, c=0 → x = 80*(1 - sqrt(1-U)).
    """
    return [int(80.0 * (1.0 - math.sqrt(max(0.0, 1.0 - rv.uniform()))) * 12)
            for _ in range(n)]


AGE_STRATEGIES = {
    "U(0,100)":   _ages_uniform_0_100,
    "U(0,40)":    _ages_uniform_0_40,
    "Triangular": _ages_triangular,
}


# ── Patched simulator for custom age distribution ─────────────────────────

class _SimulatorWithAges(Simulator):
    """Simulator that accepts a custom age-generation function."""

    def __init__(self, n_women, n_men, years, seed, death_mode, pregnancy_mode, age_fn):
        self._age_fn = age_fn
        super().__init__(n_women, n_men, years=years, seed=seed,
                         death_mode=death_mode, pregnancy_mode=pregnancy_mode)

    def _init_population(self, n: int, sex: str) -> None:
        from sim.person import Person
        for age_m in self._age_fn(n):
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
    pregnancy_mode: str = "range",
    sim_mode: str = "step",
) -> list[dict]:
    """
    Sensitivity sweep over population sizes and age distributions.

    Returns a list of result dicts, one per (size, strategy) combination:
      {
        "n_total":         int,
        "age_strategy":    str,
        "avg_extinction":  float | None,
        "survival_rate":   float,
        "avg_final_pop":   float,
        "std_final_pop":   float,
        "ci_final_pop":    (lo, hi),
        "avg_peak_pop":    float,
        "n_runs":          int,
        "extinction_samples": list[float],  # for hypothesis testing
      }
    Plus a trailing entry:
      {
        "hypothesis_test": {
          "comparison":   "U(0,100) vs U(0,40)",
          "t_stat":       float,
          "df":           int,
          "critical":     float,
          "decision":     str,
          "mean_ext_100": float | None,
          "mean_ext_40":  float | None,
        }
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
            extinction_years: list[int | None] = []
            final_pops: list[float] = []
            peak_pops:  list[float] = []

            for i in range(n_runs):
                seed = base_seed + i
                sim = build_simulator(
                    mode=sim_mode,
                    n_women=n_half,
                    n_men=n_half,
                    years=years,
                    seed=seed,
                    death_mode=death_mode,
                    pregnancy_mode=pregnancy_mode,
                    simulator_cls=lambda **kwargs: _SimulatorWithAges(
                        **kwargs,
                        age_fn=age_fn,
                    ),
                )
                stats = sim.run()

                ext = next((s["year"] for s in stats if s["population"] == 0), None)
                extinction_years.append(ext)
                final_pops.append(float(stats[-1]["population"]))
                peak_pops.append(float(max(s["population"] for s in stats)))

            survived     = [e for e in extinction_years if e is None]
            extinct_vals = [float(e) for e in extinction_years if e is not None]

            _, _, ci_fp = confidence_interval_95(final_pops)

            results.append({
                "n_total":            n_total,
                "age_strategy":       strategy_name,
                "avg_extinction":     statistics.mean(extinct_vals) if extinct_vals else None,
                "survival_rate":      len(survived) / n_runs,
                "avg_final_pop":      statistics.mean(final_pops),
                "std_final_pop":      statistics.stdev(final_pops) if len(final_pops) > 1 else 0.0,
                "ci_final_pop":       ci_fp,
                "avg_peak_pop":       statistics.mean(peak_pops),
                "n_runs":             n_runs,
                "extinction_samples": extinct_vals,
            })

    # ── Hypothesis test: U(0,100) vs U(0,40) on extinction year ──────────
    # Use the largest population size for the most reliable samples
    largest = max(population_sizes)
    ext_100 = next(
        (r["extinction_samples"] for r in results
         if r["n_total"] == largest and r["age_strategy"] == "U(0,100)"),
        [],
    )
    ext_40 = next(
        (r["extinction_samples"] for r in results
         if r["n_total"] == largest and r["age_strategy"] == "U(0,40)"),
        [],
    )

    ht: dict = {
        "comparison":   "U(0,100) vs U(0,40)",
        "mean_ext_100": statistics.mean(ext_100) if ext_100 else None,
        "mean_ext_40":  statistics.mean(ext_40)  if ext_40  else None,
    }
    if len(ext_100) >= 2 and len(ext_40) >= 2:
        t, df, crit, decision = welch_ttest(ext_100, ext_40)
        ht.update({"t_stat": t, "df": df, "critical": crit, "decision": decision})
    else:
        ht.update({"t_stat": None, "df": None, "critical": None,
                   "decision": "Muestras insuficientes para el test"})

    results.append({"hypothesis_test": ht})
    return results

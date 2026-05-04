"""Monte Carlo runner: execute N independent simulations and aggregate results."""

from __future__ import annotations
import statistics
from sim.simulator import Simulator


def run_n(
    n_women: int,
    n_men: int,
    n_runs: int,
    years: int = 100,
    base_seed: int = 0,
    death_mode: str = "monthly",
) -> dict:
    """
    Run `n_runs` simulations with seeds base_seed, base_seed+1, …
    Returns a dict with per-year aggregated statistics:
      {
        "years": [1, 2, …, years],
        "population":  {"mean": […], "std": […]},
        "men":         {"mean": […], "std": […]},
        "women":       {"mean": […], "std": […]},
        "births":      {"mean": […], "std": […]},
        "deaths":      {"mean": […], "std": […]},
        "couples":     {"mean": […], "std": […]},
        "avg_age":     {"mean": […], "std": […]},
        "extinction_year": [year or None per run],
        "survival_rate": float,   # fraction of runs that reach final year with pop > 0
        "n_runs": int,
      }
    """
    all_runs: list[list[dict]] = []

    for i in range(n_runs):
        seed = base_seed + i
        sim = Simulator(n_women, n_men, years=years, seed=seed, death_mode=death_mode)
        all_runs.append(sim.run())

    year_labels = [s["year"] for s in all_runs[0]]
    keys = ["population", "men", "women", "births", "deaths", "couples", "avg_age"]

    aggregated: dict = {"years": year_labels, "n_runs": n_runs}

    for key in keys:
        means, stds = [], []
        for yr_idx in range(len(year_labels)):
            vals = [run[yr_idx][key] for run in all_runs]
            means.append(statistics.mean(vals))
            stds.append(statistics.stdev(vals) if len(vals) > 1 else 0.0)
        aggregated[key] = {"mean": means, "std": stds}

    # Extinction year per run (first year with population == 0, or None)
    extinction_years = []
    for run in all_runs:
        ext = next((s["year"] for s in run if s["population"] == 0), None)
        extinction_years.append(ext)

    survived = sum(1 for e in extinction_years if e is None)
    aggregated["extinction_year"] = extinction_years
    aggregated["survival_rate"]   = survived / n_runs

    return aggregated

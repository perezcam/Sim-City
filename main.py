"""Entry point for the population simulation."""

import argparse
import csv
import os
import sys

from sim.simulator import Simulator
from visualize import plot_all


def parse_args():
    parser = argparse.ArgumentParser(description="Poblado en Evolución — simulación poblacional")
    parser.add_argument("--mujeres", type=int, default=500, help="Número inicial de mujeres")
    parser.add_argument("--hombres", type=int, default=500, help="Número inicial de hombres")
    parser.add_argument("--años",    type=int, default=100, help="Años a simular")
    parser.add_argument("--seed",    type=int, default=None, help="Semilla aleatoria")
    parser.add_argument("--csv",     type=str, default=None, help="Exportar estadísticas a CSV")
    parser.add_argument("--no-plot", action="store_true",    help="No mostrar gráficas")
    return parser.parse_args()


def print_table(stats: list[dict]) -> None:
    header = (
        f"{'Año':>4} | {'Pob':>6} | {'H':>5} | {'M':>5} | "
        f"{'Parejas':>7} | {'Nacim':>5} | {'Muertes':>7} | "
        f"{'NvParejas':>9} | {'Rupturas':>8} | {'EdadProm':>8}"
    )
    print(header)
    print("-" * len(header))
    for s in stats:
        print(
            f"{s['year']:>4} | {s['population']:>6} | {s['men']:>5} | {s['women']:>5} | "
            f"{s['couples']:>7} | {s['births']:>5} | {s['deaths']:>7} | "
            f"{s['couples_formed']:>9} | {s['breakups']:>8} | {s['avg_age']:>8.1f}"
        )


def save_csv(stats: list[dict], path: str) -> None:
    if not stats:
        return
    keys = [k for k in stats[0] if k != "age_groups"]
    ag_keys = list(stats[0]["age_groups"].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys + ag_keys)
        writer.writeheader()
        for s in stats:
            row = {k: s[k] for k in keys}
            row.update(s["age_groups"])
            writer.writerow(row)
    print(f"Estadísticas guardadas en: {path}")


def main():
    args = parse_args()

    print(
        f"Iniciando simulación: {args.mujeres} mujeres, {args.hombres} hombres, "
        f"{args.años} años, seed={args.seed}"
    )

    sim = Simulator(
        n_women=args.mujeres,
        n_men=args.hombres,
        years=args.años,
        seed=args.seed,
    )
    stats = sim.run()

    print_table(stats)

    if args.csv:
        save_csv(stats, args.csv)

    if not args.no_plot:
        plot_all(stats)


if __name__ == "__main__":
    main()

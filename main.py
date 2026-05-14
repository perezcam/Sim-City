"""Entry point for the population simulation."""

import argparse
import csv
import sys

from sim.factory import SIMULATION_MODES, build_simulator
from visualize import plot_all, plot_monte_carlo, plot_sensitivity, plot_family_tree


def parse_args():
    parser = argparse.ArgumentParser(description="Poblado en Evolución — simulación poblacional")
    parser.add_argument("--mujeres",     type=int,   default=500,       help="Número inicial de mujeres")
    parser.add_argument("--hombres",     type=int,   default=500,       help="Número inicial de hombres")
    parser.add_argument("--años",        type=int,   default=100,       help="Años a simular")
    parser.add_argument("--seed",        type=int,   default=None,      help="Semilla aleatoria")
    parser.add_argument("--death-mode",  type=str,   default="monthly", choices=["monthly", "annual"],
                        help="Modo de evaluación de muerte")
    parser.add_argument("--sim-mode",    type=str,   default="step", choices=list(SIMULATION_MODES),
                        help="Motor: step (mensual) o calendar_strong (FEL fuerte por entidad)")
    parser.add_argument("--runs",        type=int,   default=None,      help="Corridas Monte Carlo (activa modo MC)")
    parser.add_argument("--sensitivity",  action="store_true",           help="Ejecutar análisis de sensibilidad")
    parser.add_argument("--family-tree",  action="store_true",           help="Mostrar árbol genealógico de la familia más grande")
    parser.add_argument("--csv",         type=str,   default=None,      help="Exportar estadísticas a CSV")
    parser.add_argument("--save-fig",    type=str,   default=None,      help="Guardar gráficas en archivo PNG")
    parser.add_argument("--no-plot",     action="store_true",           help="No mostrar ni guardar gráficas")
    return parser.parse_args()


def print_table(stats: list[dict]) -> None:
    header = (
        f"{'Año':>4} | {'Pob':>6} | {'H':>5} | {'M':>5} | "
        f"{'Parejas':>7} | {'Nacim':>5} | {'Muertes':>7} | "
        f"{'NvParejas':>9} | {'Rupturas':>8} | {'EdadProm':>8}"
    )
    sep = "-" * len(header)
    print(header)
    print(sep)
    for s in stats:
        print(
            f"{s['year']:>4} | {s['population']:>6} | {s['men']:>5} | {s['women']:>5} | "
            f"{s['couples']:>7} | {s['births']:>5} | {s['deaths']:>7} | "
            f"{s['couples_formed']:>9} | {s['breakups']:>8} | {s['avg_age']:>8.1f}"
        )


def save_csv(stats: list[dict], path: str) -> None:
    if not stats:
        return
    keys    = [k for k in stats[0] if k != "age_groups"]
    ag_keys = list(stats[0]["age_groups"].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys + ag_keys)
        writer.writeheader()
        for s in stats:
            row = {k: s[k] for k in keys}
            row.update(s["age_groups"])
            writer.writerow(row)
    print(f"Estadísticas guardadas en: {path}")


def _progress(current: int, total: int, width: int = 40) -> None:
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    print(f"\r  [{bar}] {current}/{total}", end="", flush=True)


def run_single(args) -> None:
    print(
        f"Simulación única: {args.mujeres}M + {args.hombres}H, "
        f"{args.años} años, seed={args.seed}, death_mode={args.death_mode}, sim_mode={args.sim_mode}"
    )
    sim = build_simulator(
        mode=args.sim_mode,
        n_women=args.mujeres,
        n_men=args.hombres,
        years=args.años,
        seed=args.seed,
        death_mode=args.death_mode,
    )
    stats = sim.run()
    print_table(stats)

    if args.csv:
        save_csv(stats, args.csv)

    if not args.no_plot:
        plot_all(stats, save_path=args.save_fig)

    if args.family_tree and not args.no_plot:
        ft_path = args.save_fig.replace(".png", "_tree.png") if args.save_fig else None
        from sim.genealogy import summary, build_graph
        G = build_graph(sim.persons)
        s = summary(G)
        print(f"\nÁrbol genealógico: {s['nodes']} personas, "
              f"{s['generations']} generaciones, {s['founders']} fundadores")
        plot_family_tree(sim.persons, save_path=ft_path)


def run_monte_carlo(args) -> None:
    from sim.monte_carlo import run_n

    n = args.runs
    print(
        f"Monte Carlo: {n} corridas × "
        f"{args.mujeres}M + {args.hombres}H, {args.años} años, "
        f"death_mode={args.death_mode}, sim_mode={args.sim_mode}"
    )

    base_seed = args.seed if args.seed is not None else 0
    print(f"  Ejecutando {n} corridas…")
    mc = run_n(
        n_women=args.mujeres,
        n_men=args.hombres,
        n_runs=n,
        years=args.años,
        base_seed=base_seed,
        death_mode=args.death_mode,
        sim_mode=args.sim_mode,
    )

    survived = sum(1 for e in mc["extinction_year"] if e is None)
    ext_vals = [e for e in mc["extinction_year"] if e is not None]

    print(f"\nResultados Monte Carlo ({n} corridas):")
    print(f"  Supervivencia al año {args.años}: {survived}/{n} ({100*survived/n:.0f}%)")
    if ext_vals:
        import statistics
        print(f"  Año extinción — media: {statistics.mean(ext_vals):.1f}, "
              f"min: {min(ext_vals)}, max: {max(ext_vals)}")
        if mc["ci_extinction"]:
            lo, hi = mc["ci_extinction"]
            print(f"  IC 95% extinción: [{lo:.1f}, {hi:.1f}]")
    ci_lo, ci_hi = mc["ci_population"]
    print(f"  Población final — media: {mc['population']['mean'][-1]:.1f}, "
          f"std: {mc['population']['std'][-1]:.1f}")
    print(f"  IC 95% población final: [{ci_lo:.1f}, {ci_hi:.1f}]")
    print(f"  Réplicas mínimas recomendadas (error rel. 5%): {mc['min_reps']}")

    if not args.no_plot:
        plot_monte_carlo(mc, save_path=args.save_fig)


def run_sensitivity_analysis(args) -> None:
    from sim.sensitivity import run_sensitivity

    print("Análisis de sensibilidad en curso (esto puede tardar varios minutos)…")
    results = run_sensitivity(
        n_runs=10,
        years=args.años,
        death_mode=args.death_mode,
        sim_mode=args.sim_mode,
    )

    # Separate hypothesis-test entry from scenario rows
    ht_entry = next((r for r in results if "hypothesis_test" in r), None)
    scenario_results = [r for r in results if "hypothesis_test" not in r]

    print(f"\n{'Tamaño':>8} | {'Distribución':>12} | {'Superviv.':>9} | "
          f"{'Extinción':>9} | {'Pob.Final':>9} | {'IC 95% Pob.Final':>20}")
    print("-" * 83)
    for r in scenario_results:
        ext = f"{r['avg_extinction']:.1f}" if r["avg_extinction"] is not None else "  —"
        lo, hi = r["ci_final_pop"]
        print(
            f"{r['n_total']:>8} | {r['age_strategy']:>12} | "
            f"{r['survival_rate']:>8.0%} | {ext:>9} | "
            f"{r['avg_final_pop']:>9.1f} | [{lo:>6.1f}, {hi:>6.1f}]"
        )

    if ht_entry:
        ht = ht_entry["hypothesis_test"]
        print(f"\nPrueba de hipótesis — {ht['comparison']}:")
        print(f"  Media extinción U(0,100): "
              f"{ht['mean_ext_100']:.1f}" if ht["mean_ext_100"] else "  Media extinción U(0,100): —")
        print(f"  Media extinción U(0,40):  "
              f"{ht['mean_ext_40']:.1f}"  if ht["mean_ext_40"]  else "  Media extinción U(0,40):  —")
        if ht["t_stat"] is not None:
            print(f"  t de Welch = {ht['t_stat']:.3f}, df = {ht['df']}, "
                  f"valor crítico = {ht['critical']:.3f}")
            print(f"  Conclusión (α=0.05): {ht['decision']}")
        else:
            print(f"  {ht['decision']}")

    if not args.no_plot:
        plot_sensitivity(scenario_results, save_path=args.save_fig)


def main():
    args = parse_args()

    if args.sensitivity:
        run_sensitivity_analysis(args)
    elif args.runs is not None:
        run_monte_carlo(args)
    else:
        run_single(args)


if __name__ == "__main__":
    main()

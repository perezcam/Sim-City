"""Matplotlib visualizations for simulation results."""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker


def plot_all(stats: list[dict], save_path: str | None = None) -> None:
    """Generate all charts from simulation stats. Display or save to file."""
    years      = [s["year"]           for s in stats]
    population = [s["population"]     for s in stats]
    men        = [s["men"]            for s in stats]
    women      = [s["women"]          for s in stats]
    births     = [s["births"]         for s in stats]
    deaths     = [s["deaths"]         for s in stats]
    couples    = [s["couples"]        for s in stats]
    breakups   = [s["breakups"]       for s in stats]
    formed     = [s["couples_formed"] for s in stats]
    avg_age    = [s["avg_age"]        for s in stats]

    fig = plt.figure(figsize=(18, 14))
    fig.suptitle("Poblado en Evolución — Resultados de Simulación", fontsize=16, y=0.98)
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.3)

    # 1. Total population
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(years, population, color="steelblue", linewidth=2)
    ax1.set_title("Población Total")
    ax1.set_xlabel("Año")
    ax1.set_ylabel("Personas")
    ax1.grid(True, alpha=0.3)

    # 2. Men vs Women
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(years, men,   label="Hombres", color="royalblue",  linewidth=2)
    ax2.plot(years, women, label="Mujeres", color="crimson",    linewidth=2)
    ax2.set_title("Hombres vs Mujeres")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Personas")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Births and deaths
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.bar(years, births, label="Nacimientos", color="seagreen",  alpha=0.7)
    ax3.bar(years, deaths, label="Muertes",     color="firebrick", alpha=0.7)
    ax3.set_title("Nacimientos y Muertes por Año")
    ax3.set_xlabel("Año")
    ax3.set_ylabel("Cantidad")
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis="y")

    # 4. Couples activity
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(years, couples,  label="Parejas activas",  color="darkorange", linewidth=2)
    ax4.plot(years, formed,   label="Nuevas parejas",   color="gold",       linewidth=1.5, linestyle="--")
    ax4.plot(years, breakups, label="Rupturas",         color="purple",     linewidth=1.5, linestyle=":")
    ax4.set_title("Dinámica de Parejas")
    ax4.set_xlabel("Año")
    ax4.set_ylabel("Cantidad")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # 5. Average age
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.plot(years, avg_age, color="teal", linewidth=2)
    ax5.set_title("Edad Promedio de la Población")
    ax5.set_xlabel("Año")
    ax5.set_ylabel("Edad (años)")
    ax5.grid(True, alpha=0.3)

    # 6. Age pyramid at final year
    ax6 = fig.add_subplot(gs[2, 1])
    _plot_age_pyramid(ax6, stats[-1])

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Gráficas guardadas en: {save_path}")
    else:
        plt.show()


def _plot_age_pyramid(ax: plt.Axes, final_stat: dict) -> None:
    groups = list(final_stat["age_groups"].keys())
    counts = list(final_stat["age_groups"].values())
    colors = ["#5b9bd5", "#ed7d31", "#a9d18e", "#ffc000"]

    bars = ax.barh(groups, counts, color=colors, edgecolor="white", height=0.6)
    ax.set_title("Distribución de Edades (Año Final)")
    ax.set_xlabel("Personas")
    ax.grid(True, alpha=0.3, axis="x")

    ref = max(counts) if max(counts) > 0 else 1
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + ref * 0.01,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center",
            fontsize=9,
        )


# ── Monte Carlo charts ─────────────────────────────────────────────────────

def plot_monte_carlo(mc: dict, save_path: str | None = None) -> None:
    """
    Visualize aggregated Monte Carlo results.
    `mc` is the dict returned by sim.monte_carlo.run_n().
    """
    years  = mc["years"]
    n_runs = mc["n_runs"]

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(
        f"Análisis Monte Carlo — {n_runs} corridas",
        fontsize=15, y=0.98,
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # 1. Population with confidence band
    ax1 = fig.add_subplot(gs[0, :2])
    mean = mc["population"]["mean"]
    std  = mc["population"]["std"]
    lo   = [max(0, m - s) for m, s in zip(mean, std)]
    hi   = [m + s          for m, s in zip(mean, std)]
    ax1.plot(years, mean, color="steelblue", linewidth=2, label="Media")
    ax1.fill_between(years, lo, hi, alpha=0.25, color="steelblue", label="±1σ")
    ax1.set_title("Población Total (media ± 1σ)")
    ax1.set_xlabel("Año")
    ax1.set_ylabel("Personas")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Extinction year histogram
    ax2 = fig.add_subplot(gs[0, 2])
    ext_vals = [e for e in mc["extinction_year"] if e is not None]
    survived = n_runs - len(ext_vals)
    if ext_vals:
        ax2.hist(ext_vals, bins=20, color="firebrick", alpha=0.75, edgecolor="white")
    ax2.set_title(
        f"Año de extinción\n({survived}/{n_runs} corridas sobreviven)"
    )
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Corridas")
    ax2.grid(True, alpha=0.3, axis="y")

    # 3. Births mean ± std
    ax3 = fig.add_subplot(gs[1, 0])
    bm = mc["births"]["mean"]
    bs = mc["births"]["std"]
    ax3.plot(years, bm, color="seagreen", linewidth=2)
    ax3.fill_between(years,
                     [max(0, m-s) for m,s in zip(bm,bs)],
                     [m+s for m,s in zip(bm,bs)],
                     alpha=0.25, color="seagreen")
    ax3.set_title("Nacimientos / año (media ± 1σ)")
    ax3.set_xlabel("Año")
    ax3.set_ylabel("Nacimientos")
    ax3.grid(True, alpha=0.3)

    # 4. Deaths mean ± std
    ax4 = fig.add_subplot(gs[1, 1])
    dm = mc["deaths"]["mean"]
    ds = mc["deaths"]["std"]
    ax4.plot(years, dm, color="firebrick", linewidth=2)
    ax4.fill_between(years,
                     [max(0, m-s) for m,s in zip(dm,ds)],
                     [m+s for m,s in zip(dm,ds)],
                     alpha=0.25, color="firebrick")
    ax4.set_title("Muertes / año (media ± 1σ)")
    ax4.set_xlabel("Año")
    ax4.set_ylabel("Muertes")
    ax4.grid(True, alpha=0.3)

    # 5. Average age mean ± std
    ax5 = fig.add_subplot(gs[1, 2])
    am = mc["avg_age"]["mean"]
    as_ = mc["avg_age"]["std"]
    ax5.plot(years, am, color="teal", linewidth=2)
    ax5.fill_between(years,
                     [max(0, m-s) for m,s in zip(am,as_)],
                     [m+s for m,s in zip(am,as_)],
                     alpha=0.25, color="teal")
    ax5.set_title("Edad promedio (media ± 1σ)")
    ax5.set_xlabel("Año")
    ax5.set_ylabel("Edad (años)")
    ax5.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Gráfica Monte Carlo guardada en: {save_path}")
    else:
        plt.show()
    plt.close(fig)


# ── Sensitivity charts ─────────────────────────────────────────────────────

def plot_sensitivity(results: list[dict], save_path: str | None = None) -> None:
    """
    Visualize sensitivity analysis results.
    `results` is the list returned by sim.sensitivity.run_sensitivity().
    """
    strategies = sorted({r["age_strategy"] for r in results})
    sizes      = sorted({r["n_total"]      for r in results})
    colors     = ["steelblue", "seagreen", "darkorange", "crimson"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Análisis de Sensibilidad — Tamaño inicial y distribución de edades",
                 fontsize=14, y=1.02)

    metrics = [
        ("avg_final_pop",  "std_final_pop", "Población final promedio",   axes[0]),
        ("survival_rate",  None,            "Tasa de supervivencia",      axes[1]),
        ("avg_extinction", None,            "Año de extinción promedio",  axes[2]),
    ]

    x = range(len(sizes))
    width = 0.25

    for col_idx, (key, std_key, title, ax) in enumerate(metrics):
        for s_idx, strategy in enumerate(strategies):
            vals = []
            errs = []
            for size in sizes:
                row = next(r for r in results
                           if r["n_total"] == size and r["age_strategy"] == strategy)
                v = row[key]
                vals.append(v if v is not None else 0)
                if std_key:
                    errs.append(row.get(std_key, 0))

            offset = [xi + s_idx * width - width for xi in x]
            bars = ax.bar(
                offset, vals,
                width=width * 0.9,
                label=strategy,
                color=colors[s_idx % len(colors)],
                alpha=0.8,
            )
            if std_key and errs:
                ax.errorbar(offset, vals, yerr=errs, fmt="none",
                            color="black", capsize=3, linewidth=1)

        ax.set_title(title)
        ax.set_xticks(list(x))
        ax.set_xticklabels([str(s) for s in sizes])
        ax.set_xlabel("Población inicial")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Gráfica de sensibilidad guardada en: {save_path}")
    else:
        plt.show()
    plt.close(fig)


# ── Family tree chart ──────────────────────────────────────────────────────

def plot_family_tree(
    persons: dict,
    save_path: str | None = None,
    max_nodes: int = 300,
) -> None:
    """
    Draw the genealogy of the largest family found in `persons`.
    Nodes are colored by sex (blue=M, red=F) and sized by number of children.
    """
    import networkx as nx
    from sim.genealogy import build_graph, largest_family_subgraph, generation_depths

    G_full = build_graph(persons)
    G      = largest_family_subgraph(G_full)

    if G.number_of_nodes() == 0:
        print("No hay árbol genealógico para mostrar (ningún nacimiento registrado).")
        return

    # Limit size for readability
    if G.number_of_nodes() > max_nodes:
        nodes = list(G.nodes)[:max_nodes]
        G = G.subgraph(nodes).copy()

    depths = generation_depths(G)
    n_gen  = max(depths.values(), default=0) + 1

    # Hierarchical layout: x = position within generation, y = generation depth
    gen_members: dict[int, list[int]] = {}
    for node, depth in depths.items():
        gen_members.setdefault(depth, []).append(node)

    pos: dict[int, tuple] = {}
    for depth, members in gen_members.items():
        for i, node in enumerate(sorted(members)):
            pos[node] = (i - len(members) / 2, -depth)

    node_colors = [
        "#4a90d9" if G.nodes[n].get("sex") == "M" else "#e05c72"
        for n in G.nodes
    ]
    node_sizes = [
        200 + G.nodes[n].get("children_count", 0) * 80
        for n in G.nodes
    ]

    fig, ax = plt.subplots(figsize=(max(14, n_gen * 3), max(8, len(G.nodes) // 6)))
    nx.draw(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edge_color="#aaaaaa",
        arrows=True,
        arrowsize=8,
        with_labels=False,
        alpha=0.85,
    )

    # Legend
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#4a90d9", label="Hombre"),
        Patch(facecolor="#e05c72", label="Mujer"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=10)
    ax.set_title(
        f"Árbol Genealógico — Familia más grande\n"
        f"{G.number_of_nodes()} personas · {n_gen} generaciones",
        fontsize=13,
    )

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Árbol genealógico guardado en: {save_path}")
    else:
        plt.show()
    plt.close(fig)

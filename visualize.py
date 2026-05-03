"""Matplotlib visualizations for simulation results."""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


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

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center",
            fontsize=9,
        )

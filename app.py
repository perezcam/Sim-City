"""Streamlit dashboard — Poblado en Evolución."""

import io
import csv
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Poblado en Evolución",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏘️ Poblado en Evolución")
st.caption("Simulación de Eventos Discretos · Dinámica Poblacional · 100 años")

# ── Sidebar — shared parameters ────────────────────────────────────────────
with st.sidebar:
    st.header("Parámetros")
    n_mujeres   = st.slider("Mujeres iniciales",  50, 2000, 300, step=50)
    n_hombres   = st.slider("Hombres iniciales",  50, 2000, 300, step=50)
    años        = st.slider("Años a simular",      10, 100,   50, step=5)
    seed        = st.number_input("Semilla aleatoria", value=42, step=1)
    _death_label = st.radio(
        "Evaluación de muertes",
        ["Mensual (12 Bernoulli/año)", "Anual (1 Bernoulli/año)"],
        index=0,
        help=(
            "La probabilidad siempre se deriva de la tabla acumulada por rango.\n"
            "Solo cambia cuántas veces por año se lanza el dado por persona.\n"
            "Ambas son equivalentes en esperanza matemática."
        ),
    )
    death_mode = "monthly" if _death_label.startswith("Mensual") else "annual"
    sim_mode = st.radio(
        "Motor de simulación",
        ["step", "calendar_strong"],
        index=1,
        help=(
            "step     → bucle mensual clásico por fases.\n"
            "calendar_strong → FEL fuerte por entidad (next-event)."
        ),
    )
    pregnancy_mode  = st.radio(
        "Probabilidad de embarazo",
        ["range", "annual", "monthly"],
        index=1,
        help=(
            "range   → prob. acumulada en el rango de edad (como mortalidad)\n"
            "annual  → tasa anual convertida a mensual\n"
            "monthly → valor de la tabla usado directamente cada mes"
        ),
    )

    st.divider()
    st.subheader("Monte Carlo")
    n_runs = st.slider("Número de corridas", 5, 50, 20, step=5)

    st.divider()
    st.subheader("Sensibilidad")
    sens_n_runs = st.slider("Corridas por configuración", 5, 30, 10, step=5)


# ── Helpers ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cached_single(n_women, n_men, years, seed, death_mode, pregnancy_mode, sim_mode):
    from sim.factory import build_simulator
    sim = build_simulator(mode=sim_mode, n_women=n_women, n_men=n_men, years=years, seed=seed,
                          death_mode=death_mode, pregnancy_mode=pregnancy_mode)
    stats = sim.run()
    persons = sim.persons
    return stats, persons


@st.cache_data(show_spinner=False)
def cached_monte_carlo(n_women, n_men, n_runs, years, base_seed, death_mode, pregnancy_mode, sim_mode):
    from sim.monte_carlo import run_n
    return run_n(n_women, n_men, n_runs, years=years,
                 base_seed=base_seed, death_mode=death_mode,
                 pregnancy_mode=pregnancy_mode, sim_mode=sim_mode)


@st.cache_data(show_spinner=False)
def cached_sensitivity(n_runs, years, death_mode, pregnancy_mode, sim_mode):
    from sim.sensitivity import run_sensitivity
    return run_sensitivity(n_runs=n_runs, years=years,
                           death_mode=death_mode, pregnancy_mode=pregnancy_mode,
                           sim_mode=sim_mode)


def fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def stats_to_csv_bytes(stats: list[dict]) -> bytes:
    buf = io.StringIO()
    keys    = [k for k in stats[0] if k != "age_groups"]
    ag_keys = list(stats[0]["age_groups"].keys())
    writer  = csv.DictWriter(buf, fieldnames=keys + ag_keys)
    writer.writeheader()
    for s in stats:
        row = {k: s[k] for k in keys}
        row.update(s["age_groups"])
        writer.writerow(row)
    return buf.getvalue().encode()


# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Simulación", "🎲 Monte Carlo", "🌳 Árbol Genealógico"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Single simulation
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Simulación Única")

    if st.button("▶ Simular", key="btn_single"):
        with st.spinner("Corriendo simulación…"):
            stats, persons = cached_single(
                n_mujeres, n_hombres, años, int(seed), death_mode, pregnancy_mode, sim_mode
            )
        st.session_state["stats_single"]   = stats
        st.session_state["persons_single"] = persons

    if "stats_single" in st.session_state:
        stats = st.session_state["stats_single"]

        # KPI cards
        final = stats[-1]
        peak  = max(stats, key=lambda s: s["population"])
        ext   = next((s["year"] for s in stats if s["population"] == 0), None)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Población final",   final["population"])
        c2.metric("Pico poblacional",  peak["population"], f"año {peak['year']}")
        c3.metric("Extinción",         f"año {ext}" if ext else "No")
        c4.metric("Edad promedio final", f"{final['avg_age']:.1f} años")

        # Charts
        from visualize import plot_all
        fig_all = plt.figure(figsize=(18, 14))
        plt.close(fig_all)

        # Rebuild figure capturing it
        import matplotlib.gridspec as gridspec

        years_list  = [s["year"]           for s in stats]
        population  = [s["population"]     for s in stats]
        men         = [s["men"]            for s in stats]
        women       = [s["women"]          for s in stats]
        births      = [s["births"]         for s in stats]
        deaths      = [s["deaths"]         for s in stats]
        couples     = [s["couples"]        for s in stats]
        breakups    = [s["breakups"]       for s in stats]
        formed      = [s["couples_formed"] for s in stats]
        avg_age     = [s["avg_age"]        for s in stats]

        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        fig.suptitle("Resultados de Simulación", fontsize=14)

        axes[0,0].plot(years_list, population, color="steelblue", lw=2)
        axes[0,0].set_title("Población Total"); axes[0,0].grid(alpha=0.3)

        axes[0,1].plot(years_list, men,   label="Hombres", color="royalblue", lw=2)
        axes[0,1].plot(years_list, women, label="Mujeres", color="crimson",   lw=2)
        axes[0,1].set_title("Hombres vs Mujeres"); axes[0,1].legend(); axes[0,1].grid(alpha=0.3)

        axes[1,0].bar(years_list, births, label="Nacimientos", color="seagreen",  alpha=0.7)
        axes[1,0].bar(years_list, deaths, label="Muertes",     color="firebrick", alpha=0.7)
        axes[1,0].set_title("Nacimientos y Muertes"); axes[1,0].legend(); axes[1,0].grid(alpha=0.3, axis="y")

        axes[1,1].plot(years_list, couples,  label="Activas",  color="darkorange", lw=2)
        axes[1,1].plot(years_list, formed,   label="Nuevas",   color="gold",       lw=1.5, ls="--")
        axes[1,1].plot(years_list, breakups, label="Rupturas", color="purple",     lw=1.5, ls=":")
        axes[1,1].set_title("Dinámica de Parejas"); axes[1,1].legend(); axes[1,1].grid(alpha=0.3)

        axes[2,0].plot(years_list, avg_age, color="teal", lw=2)
        axes[2,0].set_title("Edad Promedio"); axes[2,0].grid(alpha=0.3)

        groups = list(stats[-1]["age_groups"].keys())
        counts = list(stats[-1]["age_groups"].values())
        axes[2,1].barh(groups, counts, color=["#5b9bd5","#ed7d31","#a9d18e","#ffc000"], height=0.6)
        axes[2,1].set_title("Distribución de Edades (Año Final)"); axes[2,1].grid(alpha=0.3, axis="x")

        fig.tight_layout()
        st.pyplot(fig)

        # Downloads
        col_a, col_b = st.columns(2)
        col_a.download_button(
            "⬇ Descargar CSV",
            data=stats_to_csv_bytes(stats),
            file_name="simulacion.csv",
            mime="text/csv",
        )
        col_b.download_button(
            "⬇ Descargar PNG",
            data=fig_to_bytes(fig),
            file_name="simulacion.png",
            mime="image/png",
        )
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Monte Carlo
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Análisis Monte Carlo")
    st.caption(f"Ejecuta {n_runs} corridas independientes y muestra la banda de confianza media ± 1σ.")

    if st.button("▶ Correr Monte Carlo", key="btn_mc"):
        with st.spinner(f"Corriendo {n_runs} simulaciones…"):
            mc = cached_monte_carlo(
                n_mujeres, n_hombres, n_runs, años, int(seed), death_mode, pregnancy_mode, sim_mode
            )
        st.session_state["mc"] = mc

    if "mc" in st.session_state:
        mc = st.session_state["mc"]

        survived  = sum(1 for e in mc["extinction_year"] if e is None)
        ext_vals  = [e for e in mc["extinction_year"] if e is not None]

        ci_lo, ci_hi = mc["ci_population"]
        ext_ci       = mc["ci_extinction"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tasa de supervivencia", f"{100*survived/n_runs:.0f}%")
        c2.metric("Extinción media",       f"año {sum(ext_vals)/len(ext_vals):.1f}" if ext_vals else "—")
        c3.metric("Población final media", f"{mc['population']['mean'][-1]:.1f}")
        c4.metric("Réplicas mín. (5% err)", str(mc["min_reps"]))

        st.caption(
            f"IC 95% población final: **[{ci_lo:.1f}, {ci_hi:.1f}]**"
            + (f"  ·  IC 95% extinción: **[{ext_ci[0]:.1f}, {ext_ci[1]:.1f}]**"
               if ext_ci else "")
        )

        from visualize import plot_monte_carlo
        years_mc = mc["years"]

        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        fig.suptitle(f"Monte Carlo — {n_runs} corridas", fontsize=13)

        def band(ax, years, key, color, title):
            mean = mc[key]["mean"]
            std  = mc[key]["std"]
            lo   = [max(0, m-s) for m,s in zip(mean,std)]
            hi   = [m+s          for m,s in zip(mean,std)]
            ax.plot(years, mean, color=color, lw=2, label="Media")
            ax.fill_between(years, lo, hi, alpha=0.25, color=color, label="±1σ")
            ax.set_title(title); ax.legend(fontsize=8); ax.grid(alpha=0.3)

        band(axes[0,0], years_mc, "population", "steelblue",  "Población total")
        band(axes[0,1], years_mc, "births",     "seagreen",   "Nacimientos / año")
        band(axes[0,2], years_mc, "deaths",     "firebrick",  "Muertes / año")
        band(axes[1,0], years_mc, "men",        "royalblue",  "Hombres")
        band(axes[1,1], years_mc, "women",      "crimson",    "Mujeres")
        band(axes[1,2], years_mc, "avg_age",    "teal",       "Edad promedio")

        fig.tight_layout()
        st.pyplot(fig)

        if ext_vals:
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            ax2.hist(ext_vals, bins=min(20, len(ext_vals)),
                     color="firebrick", alpha=0.75, edgecolor="white")
            ax2.set_title(f"Distribución del año de extinción ({len(ext_vals)}/{n_runs} corridas)")
            ax2.set_xlabel("Año"); ax2.set_ylabel("Corridas"); ax2.grid(alpha=0.3, axis="y")
            st.pyplot(fig2)
            plt.close(fig2)

        st.download_button(
            "⬇ Descargar PNG Monte Carlo",
            data=fig_to_bytes(fig),
            file_name="monte_carlo.png",
            mime="image/png",
        )
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Family tree
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Árbol Genealógico")
    st.caption("Visualiza la familia más grande generada en la simulación.")

    max_nodes = st.slider("Máximo de nodos a mostrar", 50, 500, 200, step=50)

    if st.button("▶ Generar árbol", key="btn_tree"):
        with st.spinner("Corriendo simulación y construyendo árbol…"):
            stats_t, persons_t = cached_single(
                n_mujeres, n_hombres, años, int(seed), death_mode, pregnancy_mode, sim_mode
            )
        st.session_state["persons_tree"] = persons_t

    if "persons_tree" in st.session_state:
        persons = st.session_state["persons_tree"]

        from sim.genealogy import build_graph, largest_family_subgraph, summary, max_generations
        G    = build_graph(persons)
        sub  = largest_family_subgraph(G)
        s    = summary(G)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Personas en el grafo",    s["nodes"])
        c2.metric("Generaciones (máx)",      s["generations"])
        c3.metric("Fundadores",              s["founders"])
        c4.metric("Familia más grande",      sub.number_of_nodes())

        from visualize import plot_family_tree
        import networkx as nx

        if sub.number_of_nodes() == 0:
            st.warning("No se registraron nacimientos. Aumenta los años o la población inicial.")
        else:
            # Build figure
            from sim.genealogy import generation_depths, subtree_bfs
            if sub.number_of_nodes() > max_nodes:
                sub = subtree_bfs(sub, max_nodes)

            depths    = generation_depths(sub)
            gen_members: dict = {}
            for node, depth in depths.items():
                gen_members.setdefault(depth, []).append(node)

            pos = {}
            for depth, members in gen_members.items():
                for i, node in enumerate(sorted(members)):
                    pos[node] = (i - len(members)/2, -depth)

            node_colors = [
                "#4a90d9" if sub.nodes[n].get("sex") == "M" else "#e05c72"
                for n in sub.nodes
            ]
            node_sizes = [
                200 + sub.nodes[n].get("children_count", 0) * 80
                for n in sub.nodes
            ]

            n_gen = max(depths.values(), default=0) + 1
            fig, ax = plt.subplots(figsize=(16, max(6, n_gen * 2)))
            nx.draw(
                sub, pos, ax=ax,
                node_color=node_colors, node_size=node_sizes,
                edge_color="#aaaaaa", arrows=True, arrowsize=8,
                with_labels=False, alpha=0.85,
            )
            from matplotlib.patches import Patch
            ax.legend(handles=[
                Patch(facecolor="#4a90d9", label="Hombre"),
                Patch(facecolor="#e05c72", label="Mujer"),
            ], loc="upper right")
            ax.set_title(
                f"Familia más grande — {sub.number_of_nodes()} personas · {n_gen} generaciones",
                fontsize=12,
            )

            st.pyplot(fig)
            st.download_button(
                "⬇ Descargar árbol PNG",
                data=fig_to_bytes(fig),
                file_name="arbol_genealogico.png",
                mime="image/png",
            )
            plt.close(fig)

        # GEXF export
        buf_gexf = io.BytesIO()
        nx.write_gexf(G, buf_gexf)
        st.download_button(
            "⬇ Descargar GEXF (Gephi)",
            data=buf_gexf.getvalue(),
            file_name="genealogia.gexf",
            mime="application/xml",
        )

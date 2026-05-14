"""Build and export family-tree graphs from simulation data."""

from __future__ import annotations
import networkx as nx
from sim.person import Person


def build_graph(persons: dict[int, Person]) -> nx.DiGraph:
    """
    Build a directed genealogy graph.
    Nodes: person ids.
    Edges: parent → child (father→child and mother→child).
    Node attributes: sex, birth_year, alive, age_months, children_count.
    """
    G = nx.DiGraph()

    for p in persons.values():
        G.add_node(
            p.id,
            sex=p.sex,
            birth_year=p.birth_year,
            alive=p.alive,
            age_months=p.age_months,
            children_count=p.children_count,
        )

    for p in persons.values():
        if p.father_id is not None and p.father_id in persons:
            G.add_edge(p.father_id, p.id, relation="father")
        if p.mother_id is not None and p.mother_id in persons:
            G.add_edge(p.mother_id, p.id, relation="mother")

    return G


def largest_family_subgraph(G: nx.DiGraph) -> nx.DiGraph:
    """Return the connected component with the most nodes."""
    undirected = G.to_undirected()
    components = list(nx.connected_components(undirected))
    if not components:
        return G
    biggest = max(components, key=len)
    return G.subgraph(biggest).copy()


def generation_depths(G: nx.DiGraph) -> dict[int, int]:
    """
    Assign a generation depth to each node (0 = founding generation,
    1 = their children, etc.).
    """
    depths: dict[int, int] = {}
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    for root in roots:
        for node in nx.descendants(G, root) | {root}:
            d = nx.shortest_path_length(G, root, node) if nx.has_path(G, root, node) else 0
            depths[node] = max(depths.get(node, 0), d)
    return depths


def max_generations(G: nx.DiGraph) -> int:
    """Return the maximum number of generations in the graph."""
    depths = generation_depths(G)
    return max(depths.values(), default=0) + 1


def subtree_bfs(G: nx.DiGraph, max_nodes: int) -> nx.DiGraph:
    """
    Return a subgraph of at most max_nodes nodes that preserves generational
    structure.  Picks the founder with the most descendants and expands via BFS.
    """
    roots = [n for n in G.nodes if G.in_degree(n) == 0]
    if not roots:
        nodes = list(G.nodes)[:max_nodes]
        return G.subgraph(nodes).copy()

    # Choose the founder whose subtree is largest
    best_root = max(roots, key=lambda r: len(nx.descendants(G, r)))

    visited: list[int] = []
    queue = [best_root]
    seen: set[int] = {best_root}
    while queue and len(visited) < max_nodes:
        node = queue.pop(0)
        visited.append(node)
        for child in G.successors(node):
            if child not in seen:
                seen.add(child)
                queue.append(child)

    return G.subgraph(visited).copy()


def export_gexf(G: nx.DiGraph, path: str) -> None:
    """Export graph to GEXF format (readable by Gephi)."""
    nx.write_gexf(G, path)
    print(f"Árbol genealógico exportado a: {path}")


def summary(G: nx.DiGraph) -> dict:
    """Return a summary dict for quick inspection."""
    return {
        "nodes":       G.number_of_nodes(),
        "edges":       G.number_of_edges(),
        "generations": max_generations(G),
        "founders":    sum(1 for n in G.nodes if G.in_degree(n) == 0),
        "leaves":      sum(1 for n in G.nodes if G.out_degree(n) == 0),
    }

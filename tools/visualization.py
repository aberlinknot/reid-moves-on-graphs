"""
Visualization tools for graphs (networkx-based).

All code, comments, and docstrings must be in English (NumPy style).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


def draw_graph(
    graph: nx.Graph,
    title: str | None = None,
    with_labels: bool = True,
    layout_seed: int | None = 42,
    output_path: Path | None = None,
    show: bool = True,
) -> None:
    """
    Draw a graph using matplotlib.

    Parameters
    ----------
    graph : nx.Graph
        The graph to visualize.
    title : str, optional
        Title for the plot.
    with_labels : bool, default=True
        Whether to display node labels.
    layout_seed : int | None, default=42
        Seed for deterministic spring layout positioning.
    output_path : Path | None, default=None
        Output image path. If provided, the figure is saved to this file.
    show : bool, default=True
        Whether to display the plot window.
    """
    _, axis = plt.subplots(figsize=(7, 5))
    pos = nx.spring_layout(graph, seed=layout_seed)
    nx.draw(
        graph,
        pos,
        with_labels=with_labels,
        node_color="lightblue",
        edge_color="gray",
        node_size=600,
        ax=axis,
    )
    if title:
        axis.set_title(title)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")

    if show:
        plt.show()

    plt.close()

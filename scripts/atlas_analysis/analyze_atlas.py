"""Build atlas analysis tables for Reidemeister moves I/II/III.

This script scans all graphs from ``networkx.graph_atlas_g()``, computes
per-graph move statistics, and writes a detailed CSV table:

- ``results/tables/atlas_analysis.csv``

For each of the 1253 atlas graphs, the script computes:

- Reidemeister move I/II/III candidates and reachable result graphs
- Connectivity status (is connected)
- Stuck status (no move I or II available)
- III-class membership (equivalence classes under move III reachability)

Examples
--------
Run as module::

    python -m scripts.atlas_analysis.analyze_atlas

With custom output path::

    python -m scripts.atlas_analysis.analyze_atlas --analysis-output /tmp/atlas.csv

The output CSV contains columns:
    graph_index, num_vertices, num_edges, edges, move_1_candidates,
    move_1_results, move_2_candidates, move_2_results, move_3_candidates,
    move_3_results, is_connected, is_stuck_graph, iii_class_id,
    size_of_iii_class, is_in_stuck_class
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import networkx as nx
import pandas as pd

from src.moves.reidemeister import (
    apply_move_1_remove,
    apply_move_2_remove,
    apply_move_3,
    find_move_1_remove_candidates,
    find_move_2_remove_candidates,
    find_move_3_candidates,
)


def _atlas_signature(graph: nx.Graph) -> tuple[str, int, int]:
    """Compute a compact signature used for atlas index lookup.

    Parameters
    ----------
    graph : nx.Graph
        Graph to encode.

    Returns
    -------
    tuple[str, int, int]
        Weisfeiler-Lehman hash and basic size features.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message=(
                'The hashes produced for graphs without node or edge attributes changed in v3.5 '
                'due to a bugfix*'
            ),
            category=UserWarning,
            module='networkx.algorithms.graph_hashing',
        )
        graph_hash = nx.weisfeiler_lehman_graph_hash(graph)

    return (
        graph_hash,
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )


def _build_signature_index(atlas_graphs: list[nx.Graph]) -> dict[tuple[str, int, int], list[int]]:
    """Build reverse index from signature to candidate atlas indices.

    Parameters
    ----------
    atlas_graphs : list[nx.Graph]
        Full atlas graph list.

    Returns
    -------
    dict[tuple[str, int, int], list[int]]
        Map from graph signature to candidate atlas indices.
    """
    index: dict[tuple[str, int, int], list[int]] = {}
    for atlas_index, graph in enumerate(atlas_graphs):
        signature = _atlas_signature(graph)
        index.setdefault(signature, []).append(atlas_index)
    return index


def _resolve_atlas_index(
    graph: nx.Graph,
    atlas_graphs: list[nx.Graph],
    signature_index: dict[tuple[str, int, int], list[int]],
) -> int | None:
    """Resolve graph index in atlas for an unlabeled graph.

    Parameters
    ----------
    graph : nx.Graph
        Graph to resolve.
    atlas_graphs : list[nx.Graph]
        Full atlas graph list.
    signature_index : dict[tuple[str, int, int], list[int]]
        Signature-to-indices reverse map.

    Returns
    -------
    int | None
        Atlas index when a unique isomorphic representative is found,
        otherwise None.
    """
    signature = _atlas_signature(graph)
    candidates = signature_index.get(signature, [])
    for candidate_index in candidates:
        if nx.is_isomorphic(graph, atlas_graphs[candidate_index]):
            return candidate_index
    return None


def _is_connected(graph: nx.Graph) -> bool:
    """Return whether graph is connected, safely handling empty graph.

    Parameters
    ----------
    graph : nx.Graph
        Input graph.

    Returns
    -------
    bool
        True if graph is connected.
    """
    if graph.number_of_nodes() == 0:
        return False
    return nx.is_connected(graph)


def _format_edges(graph: nx.Graph) -> str:
    """Format graph edges as a semicolon-separated tuple list.

    Parameters
    ----------
    graph : nx.Graph
        Input graph.

    Returns
    -------
    str
        Edge list in canonical text form, for example
        ``(0, 1); (0, 2); (1, 2)``.
    """
    normalized_edges: list[tuple[int, int]] = []
    for left, right in graph.edges():
        a, b = sorted((int(left), int(right)))
        normalized_edges.append((a, b))

    normalized_edges.sort()
    return '; '.join(f'({left}, {right})' for left, right in normalized_edges)


def _collect_one_step_results(
    graph: nx.Graph,
    atlas_graphs: list[nx.Graph],
    signature_index: dict[tuple[str, int, int], list[int]],
) -> tuple[
    list[int],
    list[tuple[int, int]],
    list[tuple[int, int, int]],
    list[int],
    list[int],
    list[int],
]:
    """Collect move candidates and corresponding atlas result indices.

    Parameters
    ----------
    graph : nx.Graph
        Source graph.
    atlas_graphs : list[nx.Graph]
        Full atlas graph list.
    signature_index : dict[tuple[str, int, int], list[int]]
        Signature-to-indices reverse map.

    Returns
    -------
    tuple
        Tuple of (move_1_candidates, move_2_candidates, move_3_candidates,
        move_1_results, move_2_results, move_3_results). Each candidates list
        contains node/edge identifiers; each results list contains atlas
        indices of reachable graphs.
    """
    move_1_candidates = find_move_1_remove_candidates(graph)
    move_2_candidates = find_move_2_remove_candidates(graph)
    move_3_candidates = find_move_3_candidates(graph)

    move_1_results: list[int] = []
    move_2_results: list[int] = []
    move_3_results: list[int] = []

    for node in move_1_candidates:
        updated = apply_move_1_remove(graph, node)
        idx = _resolve_atlas_index(updated, atlas_graphs, signature_index)
        if idx is not None:
            move_1_results.append(idx)

    for left, right in move_2_candidates:
        updated = apply_move_2_remove(graph, left, right)
        idx = _resolve_atlas_index(updated, atlas_graphs, signature_index)
        if idx is not None:
            move_2_results.append(idx)

    for first, second, third in move_3_candidates:
        updated = apply_move_3(graph, first, second, third)
        idx = _resolve_atlas_index(updated, atlas_graphs, signature_index)
        if idx is not None:
            move_3_results.append(idx)

    return (
        move_1_candidates,
        move_2_candidates,
        move_3_candidates,
        move_1_results,
        move_2_results,
        move_3_results,
    )


def _build_move_3_components(
    num_graphs: int, move_3_edges: list[tuple[int, int]]
) -> tuple[list[int], list[int]]:
    """Build connected components induced by move-III transitions.

    Parameters
    ----------
    num_graphs : int
        Number of atlas graphs.
    move_3_edges : list[tuple[int, int]]
        Undirected edges between atlas indices connected by one move-III step.

    Returns
    -------
    tuple[list[int], list[int]]
        Per-graph component id and component size.
    """
    relation = nx.Graph()
    relation.add_nodes_from(range(num_graphs))
    relation.add_edges_from(move_3_edges)

    class_id = [-1] * num_graphs
    class_size = [0] * num_graphs

    for comp_idx, component in enumerate(nx.connected_components(relation)):
        comp_size = len(component)
        for graph_idx in component:
            class_id[graph_idx] = comp_idx
            class_size[graph_idx] = comp_size

    return class_id, class_size


def build_atlas_analysis() -> pd.DataFrame:
    """Compute per-graph atlas analysis table.

    Returns
    -------
    pd.DataFrame
        Detailed per-graph analysis.
    """
    atlas_graphs = [graph.copy() for graph in nx.graph_atlas_g()]
    signature_index = _build_signature_index(atlas_graphs)

    records_without_class: list[dict[str, object]] = []
    move_3_edges: list[tuple[int, int]] = []

    for graph_index, graph in enumerate(atlas_graphs):
        (
            move_1_candidates,
            move_2_candidates,
            move_3_candidates,
            move_1_results,
            move_2_results,
            move_3_results,
        ) = _collect_one_step_results(graph, atlas_graphs, signature_index)

        is_connected = _is_connected(graph)
        is_stuck_graph = len(move_1_candidates) == 0 and len(move_2_candidates) == 0

        for target in move_3_results:
            move_3_edges.append((graph_index, target))

        records_without_class.append(
            {
                'graph_index': graph_index,
                'num_vertices': graph.number_of_nodes(),
                'num_edges': graph.number_of_edges(),
                'edges': _format_edges(graph),
                'move_1_candidates': str(move_1_candidates),
                'move_1_results': str(move_1_results),
                'move_2_candidates': str(move_2_candidates),
                'move_2_results': str(move_2_results),
                'move_3_candidates': str(move_3_candidates),
                'move_3_results': str(move_3_results),
                'is_connected': is_connected,
                'is_stuck_graph': is_stuck_graph,
            }
        )

    iii_class_id, iii_class_size = _build_move_3_components(len(atlas_graphs), move_3_edges)

    records: list[dict[str, object]] = []
    for row in records_without_class:
        graph_index = int(row['graph_index'])
        records.append(
            {
                'graph_index': graph_index,
                'num_vertices': int(row['num_vertices']),
                'num_edges': int(row['num_edges']),
                'edges': str(row['edges']),
                'move_1_candidates': str(row['move_1_candidates']),
                'move_1_results': str(row['move_1_results']),
                'move_2_candidates': str(row['move_2_candidates']),
                'move_2_results': str(row['move_2_results']),
                'move_3_candidates': str(row['move_3_candidates']),
                'move_3_results': str(row['move_3_results']),
                'is_connected': bool(row['is_connected']),
                'is_stuck_graph': bool(row['is_stuck_graph']),
                'iii_class_id': iii_class_id[graph_index],
                'size_of_iii_class': iii_class_size[graph_index],
            }
        )

    stuck_class_map: dict[int, bool] = {}
    for record in records:
        class_id = int(record['iii_class_id'])
        is_stuck_graph = bool(record['is_stuck_graph'])
        if class_id not in stuck_class_map:
            stuck_class_map[class_id] = is_stuck_graph
        else:
            stuck_class_map[class_id] = stuck_class_map[class_id] and is_stuck_graph

    for record in records:
        class_id = int(record['iii_class_id'])
        record['is_in_stuck_class'] = bool(stuck_class_map[class_id])

    df = pd.DataFrame(records)
    return df.sort_values('graph_index').reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns
    -------
    argparse.Namespace
        Parsed argument object.
    """
    parser = argparse.ArgumentParser(
        description='Analyze full NetworkX graph atlas and export CSV tables.'
    )
    parser.add_argument(
        '--analysis-output',
        type=Path,
        default=Path('results/tables/atlas_analysis.csv'),
        help='Path to detailed per-graph analysis CSV.',
    )
    return parser.parse_args()


def main() -> None:
    """Run atlas analysis and write a detailed CSV file.

    Loads ``networkx.graph_atlas_g()``, computes per-graph Reidemeister move
    statistics and III-class membership, and exports to CSV.

    Example
    -------
    Run with default output path (``results/tables/atlas_analysis.csv``)::

        python -m scripts.atlas_analysis.analyze_atlas

    Run with custom output::

        python -m scripts.atlas_analysis.analyze_atlas --analysis-output /custom/path.csv
    """
    args = parse_args()

    analysis_df = build_atlas_analysis()

    args.analysis_output.parent.mkdir(parents=True, exist_ok=True)

    analysis_df.to_csv(args.analysis_output, index=False)

    print(f'Analysis table written: {args.analysis_output} ({len(analysis_df)} rows)')


if __name__ == '__main__':
    main()

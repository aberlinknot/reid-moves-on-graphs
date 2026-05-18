"""Compute parity bracket invariant for all graphs in the NetworkX atlas.

For each atlas graph G with even-vertex set S = V_even(G) (vertices of even
degree), computes the parity bracket [G] and writes the results to a CSV
table.

The bracket is the F_2 sum of Schur complement graphs H_{S,alpha} over all
admissible alpha in {0, 1}^k.  Each bracket term is then reduced by
Reidemeister move 2, F_2 cancellation is applied again, and surviving terms
are mapped to atlas indices.  A final index-level F_2 cancellation removes
any remaining pairs.

Output columns
--------------
graph_index : int
    Index of the graph in ``networkx.graph_atlas_g()``.
num_vertices : int
    Number of vertices.
num_edges : int
    Number of edges.
edges : str
    Semicolon-separated edge list, e.g. ``(0, 1); (1, 2)``.
even_vertices : str
    Semicolon-separated even-degree vertex labels.  Empty string if
    S = empty set.
num_even_vertices : int
    k = |S|.
num_admissible : int
    Number of bracket terms after move-2 reduction and F_2 cancellation
    (pre-index-level cancellation).
bracket_terms : str or None
    Space-plus-separated atlas indices of surviving bracket summands, e.g.
    ``94`` or ``94 + 174``.  ``None`` if the bracket is zero.
bracket_size : int
    Number of non-cancelled summands (final).
bracket_is_trivial : bool
    True if the bracket is zero, or all surviving terms are the empty graph
    (atlas index 0) or single-vertex graph (atlas index 1).

Examples
--------
Run with default output path::

    python -m scripts.parity_bracket.atlas_parity_bracket

Run with custom output and vertex cap::

    python -m scripts.parity_bracket.atlas_parity_bracket \\
        --output results/tables/parity_bracket_atlas.csv \\
        --max-vertices 5
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import networkx as nx
import pandas as pd

from src.invariants.parity_bracket import compute_parity_bracket
from src.moves.reidemeister import find_move_2_remove_candidates, apply_move_2_remove

_DEFAULT_OUTPUT = Path('results/tables/parity_bracket_atlas.csv')


def _simplify_with_move_2(graph: nx.Graph) -> nx.Graph:
    """Apply Reidemeister move 2 remove until no candidates remain.

    Parameters
    ----------
    graph : nx.Graph
        Input graph term.

    Returns
    -------
    nx.Graph
        Fully simplified graph.
    """
    result = graph.copy()
    while True:
        candidates = find_move_2_remove_candidates(result)
        if not candidates:
            break
        left, right = candidates[0]
        result = apply_move_2_remove(result, left, right)
    return result


def _atlas_signature(graph: nx.Graph) -> tuple[str, int, int]:
    """Compute a structural signature for atlas index lookup.

    Parameters
    ----------
    graph : nx.Graph
        Input graph.

    Returns
    -------
    tuple[str, int, int]
        Tuple of (WL hash, node count, edge count).
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
        wl_hash = nx.weisfeiler_lehman_graph_hash(graph)
    return (wl_hash, graph.number_of_nodes(), graph.number_of_edges())


def _build_signature_index(
    atlas_graphs: list[nx.Graph],
) -> dict[tuple[str, int, int], list[int]]:
    """Build a reverse index from signature to atlas indices.

    Parameters
    ----------
    atlas_graphs : list[nx.Graph]
        Full atlas graph list.

    Returns
    -------
    dict[tuple[str, int, int], list[int]]
        Map from signature to candidate atlas indices.
    """
    index: dict[tuple[str, int, int], list[int]] = {}
    for atlas_index, graph in enumerate(atlas_graphs):
        sig = _atlas_signature(graph)
        index.setdefault(sig, []).append(atlas_index)
    return index


def _resolve_atlas_index(
    graph: nx.Graph,
    atlas_graphs: list[nx.Graph],
    signature_index: dict[tuple[str, int, int], list[int]],
) -> int | None:
    """Find the atlas index of a graph by isomorphism.

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
    int or None
        Atlas index of the first isomorphic representative, or None.
    """
    sig = _atlas_signature(graph)
    for candidate_idx in signature_index.get(sig, []):
        if nx.is_isomorphic(graph, atlas_graphs[candidate_idx]):
            return candidate_idx
    return None


def _format_edges(edges: list[tuple[int, int]] | nx.classes.reportviews.EdgeView) -> str:
    """Format an edge iterable as a sorted semicolon-separated string.

    Parameters
    ----------
    edges : list[tuple[int, int]] or nx EdgeView
        Edge iterable.

    Returns
    -------
    str
        Edge list string, e.g. ``(0, 1); (0, 2); (1, 2)``.
    """
    normalized_edges: list[tuple[int, int]] = []
    for u, v in edges:
        a, b = sorted((int(u), int(v)))
        normalized_edges.append((a, b))
    normalized_edges.sort()
    return '; '.join(f'({a}, {b})' for a, b in normalized_edges)


def _f2_cancel_isomorphic(graphs: list[nx.Graph]) -> list[nx.Graph]:
    """Cancel isomorphic graph terms pairwise over F_2.

    Parameters
    ----------
    graphs : list[nx.Graph]
        Graph terms to reduce.

    Returns
    -------
    list[nx.Graph]
        Surviving representatives with odd multiplicity.
    """
    if not graphs:
        return []

    grouped: dict[tuple[str, int, int], list[tuple[int, nx.Graph]]] = {}
    for graph in graphs:
        sig = _atlas_signature(graph)
        grouped.setdefault(sig, [])

        matched = False
        for idx, (parity, rep) in enumerate(grouped[sig]):
            if nx.is_isomorphic(graph, rep):
                grouped[sig][idx] = ((parity + 1) % 2, rep)
                matched = True
                break

        if not matched:
            grouped[sig].append((1, graph))

    survivors: list[nx.Graph] = []
    for bucket in grouped.values():
        for parity, rep in bucket:
            if parity == 1:
                survivors.append(rep)

    survivors.sort(key=lambda g: (g.number_of_nodes(), g.number_of_edges()))
    return survivors


def _format_nodes(nodes: list[int]) -> str:
    """Format a list of node labels as a semicolon-separated string.

    Parameters
    ----------
    nodes : list[int]
        Node labels.

    Returns
    -------
    str
        Formatted string, e.g. ``1; 3``, or empty string for empty list.
    """
    return '; '.join(str(v) for v in sorted(nodes))


def build_parity_bracket_table(max_vertices: int | None = None) -> pd.DataFrame:
    """Compute parity bracket for all atlas graphs and even-vertex subsets.

    Parameters
    ----------
    max_vertices : int or None
        If given, only process atlas graphs with at most this many vertices.
        Useful for faster runs during development.

    Returns
    -------
    pd.DataFrame
        Table with one row per graph.
    """
    atlas_graphs = [g.copy() for g in nx.graph_atlas_g()]
    signature_index = _build_signature_index(atlas_graphs)

    records: list[dict[str, object]] = []

    for graph_index, graph in enumerate(atlas_graphs):
        n = graph.number_of_nodes()
        if max_vertices is not None and n > max_vertices:
            continue

        # Even vertices = vertices with even degree (ordinary sense).
        even_vertices = [v for v in graph.nodes if graph.degree[v] % 2 == 0]

        # Step 1: compute raw bracket (F_2 sum of Schur complements).
        bracket = compute_parity_bracket(graph, even_vertices)

        # Step 2: apply move-2 reduction to each term until exhausted.
        simplified_bracket = [_simplify_with_move_2(H) for H in bracket]

        # Step 3: re-apply F_2 cancellation after simplification.
        reduced_bracket = _f2_cancel_isomorphic(simplified_bracket)

        # Step 4: map each surviving graph to its atlas index.
        bracket_indices = [
            _resolve_atlas_index(H, atlas_graphs, signature_index)
            for H in reduced_bracket
        ]

        # Step 5: index-level F_2 cancellation (cancel pairs of equal indices).
        index_counts: dict[int | None, int] = {}
        for idx in bracket_indices:
            index_counts[idx] = index_counts.get(idx, 0) + 1
        final_indices = sorted(
            [idx for idx, cnt in index_counts.items() if cnt % 2 == 1],
            key=lambda x: (x is None, x),
        )

        # Format bracket terms: None if bracket is zero, else join indices.
        bracket_terms_str: str | None
        if not final_indices:
            bracket_terms_str = None
        else:
            bracket_terms_str = ' + '.join(str(idx) for idx in final_indices)

        # Trivial if zero, or all surviving terms are empty/single-vertex graph.
        trivial_atlas_indices = {0, 1}
        is_trivial = (
            not final_indices
            or all(idx in trivial_atlas_indices for idx in final_indices)
        )

        records.append({
            'graph_index': graph_index,
            'num_vertices': n,
            'num_edges': graph.number_of_edges(),
            'edges': _format_edges(graph.edges()),
            'even_vertices': _format_nodes(even_vertices),
            'num_even_vertices': len(even_vertices),
            'num_admissible': len(reduced_bracket),
            'bracket_terms': bracket_terms_str,
            'bracket_size': len(final_indices),
            'bracket_is_trivial': is_trivial,
        })

    return pd.DataFrame(records)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns
    -------
    argparse.Namespace
        Parsed argument object.
    """
    parser = argparse.ArgumentParser(
        description='Compute parity bracket invariant for all NetworkX atlas graphs.'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=_DEFAULT_OUTPUT,
        help='Path for the output CSV table.',
    )
    parser.add_argument(
        '--max-vertices',
        type=int,
        default=None,
        metavar='N',
        help='Only process atlas graphs with at most N vertices.',
    )
    return parser.parse_args()


def main() -> None:
    """Run parity bracket atlas scan and write CSV.

    Example
    -------
    Run with default settings::

        python -m scripts.parity_bracket.atlas_parity_bracket

    Run with vertex cap for a quick test::

        python -m scripts.parity_bracket.atlas_parity_bracket --max-vertices 4
    """
    args = parse_args()

    print(f'Computing parity bracket for atlas graphs'
          + (f' (max {args.max_vertices} vertices)' if args.max_vertices else '') + '...')

    df = build_parity_bracket_table(max_vertices=args.max_vertices)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    total = len(df)
    non_zero = int((~df['bracket_is_trivial']).sum())
    print(f'Done. {total} rows written to {args.output}')
    print(f'Non-zero brackets: {non_zero} / {total}')


if __name__ == '__main__':
    main()

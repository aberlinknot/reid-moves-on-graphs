"""Render nontrivial parity bracket atlas cases as side-by-side images.

This script reads the parity bracket CSV table, recomputes the labelled surviving
term for each nontrivial case, and saves a comparison image:
- left: original atlas graph,
- right: parity bracket term.

The right graph keeps labels of surviving (non-even) original vertices, so removed
even vertices are visibly absent in numbering.

Examples
--------
Run with default paths::

    python -m scripts.parity_bracket.render_nontrivial_brackets
"""

from __future__ import annotations

import argparse
import itertools
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from src.invariants.parity_bracket import _schur_complement
from src.moves.reidemeister import apply_move_2_remove, find_move_2_remove_candidates

_DEFAULT_CSV = Path('results/tables/parity_bracket_atlas.csv')
_DEFAULT_OUTPUT_DIR = Path('results/images/nontrivial_brackets')


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


def _build_signature_index(atlas_graphs: list[nx.Graph]) -> dict[tuple[str, int, int], list[int]]:
    """Build a reverse index from signature to atlas indices."""
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
    """Resolve graph to atlas index by isomorphism."""
    sig = _atlas_signature(graph)
    for candidate_idx in signature_index.get(sig, []):
        if nx.is_isomorphic(graph, atlas_graphs[candidate_idx]):
            return candidate_idx
    return None


def _simplify_with_move_2(graph: nx.Graph) -> nx.Graph:
    """Apply move-2 remove repeatedly until no candidates remain."""
    result = graph.copy()
    while True:
        candidates = find_move_2_remove_candidates(result)
        if not candidates:
            break
        left, right = candidates[0]
        result = apply_move_2_remove(result, left, right)
    return result


def _f2_cancel_isomorphic(graphs: list[nx.Graph]) -> list[nx.Graph]:
    """Cancel isomorphic graph terms pairwise over F2."""
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


def _compute_labeled_reduced_bracket_term(graph: nx.Graph) -> nx.Graph | None:
    """Compute the surviving nontrivial bracket term with original vertex labels.

    The implementation mirrors the atlas parity bracket pipeline, but when building
    Schur terms it keeps node labels equal to odd-vertex labels of the original
    graph. This preserves visible numbering after removing even vertices.
    """
    even_nodes = [v for v in graph.nodes if graph.degree[v] % 2 == 0]
    even_set = set(even_nodes)
    odd_nodes = [v for v in graph.nodes if v not in even_set]

    all_nodes = list(even_nodes) + list(odd_nodes)
    node_to_idx = {v: i for i, v in enumerate(all_nodes)}

    n = len(all_nodes)
    k = len(even_nodes)
    A = np.zeros((n, n), dtype=np.uint8)
    for u, v in graph.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        A[i, j] = A[j, i] = 1

    terms: list[nx.Graph] = []
    for alpha in itertools.product((0, 1), repeat=k):
        A_prime = _schur_complement(A, k, alpha)
        if A_prime is None:
            continue

        H = nx.Graph()
        H.add_nodes_from(odd_nodes)
        m = len(odd_nodes)
        for i in range(m):
            for j in range(i + 1, m):
                if A_prime[i, j] == 1:
                    H.add_edge(odd_nodes[i], odd_nodes[j])
        terms.append(H)

    raw = _f2_cancel_isomorphic(terms)
    simplified = [_simplify_with_move_2(term) for term in raw]
    reduced = _f2_cancel_isomorphic(simplified)

    if not reduced:
        return None
    if len(reduced) != 1:
        raise ValueError('Expected one surviving term for nontrivial case.')
    return reduced[0]


def _save_case_image(
    original: nx.Graph,
    result: nx.Graph,
    graph_index: int,
    result_index: int | None,
    output_path: Path,
) -> None:
    """Render and save one side-by-side comparison image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=160)
    fig.patch.set_facecolor('#f5f5f5')

    # Use a shared layout seed for comparability; result keeps subset positions.
    pos_original = nx.spring_layout(original, seed=42)
    pos_result = {node: pos_original[node] for node in result.nodes if node in pos_original}
    missing = [node for node in result.nodes if node not in pos_result]
    if missing:
        fallback = nx.spring_layout(result, seed=42)
        for node in missing:
            pos_result[node] = fallback[node]

    nx.draw_networkx(
        original,
        pos=pos_original,
        ax=axes[0],
        with_labels=True,
        node_size=650,
        node_color='#b7dbea',
        edge_color='#7f7f7f',
        font_size=12,
    )
    axes[0].set_title(
        f'Original atlas[{graph_index}] (n={original.number_of_nodes()}, m={original.number_of_edges()})',
        fontsize=14,
    )
    axes[0].set_axis_off()

    nx.draw_networkx(
        result,
        pos=pos_result,
        ax=axes[1],
        with_labels=True,
        node_size=650,
        node_color='#89e58f',
        edge_color='#7f7f7f',
        font_size=12,
    )
    right_index = '?' if result_index is None else str(result_index)
    axes[1].set_title(
        f'Parity bracket term atlas[{right_index}] (n={result.number_of_nodes()}, m={result.number_of_edges()})',
        fontsize=14,
    )
    axes[1].set_axis_off()

    fig.suptitle(f'Nontrivial parity bracket case atlas[{graph_index}]', fontsize=16)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Render nontrivial parity bracket atlas examples as side-by-side images.'
    )
    parser.add_argument(
        '--csv',
        type=Path,
        default=_DEFAULT_CSV,
        help='Path to parity bracket CSV table.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help='Directory for generated images.',
    )
    return parser.parse_args()


def main() -> None:
    """Render all nontrivial cases listed in the parity bracket CSV."""
    args = parse_args()

    df = pd.read_csv(args.csv)
    nontrivial = df[df['bracket_is_trivial'] == False].copy()

    atlas_graphs = [g.copy() for g in nx.graph_atlas_g()]
    signature_index = _build_signature_index(atlas_graphs)

    rendered = 0
    for row in nontrivial.itertuples(index=False):
        graph_index = int(row.graph_index)
        original = atlas_graphs[graph_index]

        result_graph = _compute_labeled_reduced_bracket_term(original)
        if result_graph is None:
            continue

        result_index = _resolve_atlas_index(result_graph, atlas_graphs, signature_index)
        output_path = args.output_dir / (
            f'atlas_{graph_index:04d}_n{original.number_of_nodes()}_m{original.number_of_edges()}'
            f'_bracket_n{result_graph.number_of_nodes()}.png'
        )

        _save_case_image(
            original=original,
            result=result_graph,
            graph_index=graph_index,
            result_index=result_index,
            output_path=output_path,
        )
        rendered += 1

    print(f'Rendered {rendered} nontrivial images to {args.output_dir}')


if __name__ == '__main__':
    main()

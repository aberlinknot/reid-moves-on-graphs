"""Parity bracket invariant computation for graphs.

The parity bracket [G] of a graph G with a designated set of even vertices
E(G) is a formal linear combination over F_2 of graphs.  For each admissible
pair (S, alpha) with S = E(G) and alpha in {0, 1}^k, the matrix

    M = A(G) + diag(alpha_1, ..., alpha_k, 0, ..., 0)

is reduced to block form via elementary row and column operations of the
third type over F_2.  The resulting bottom-right block A' is the Schur
complement of the top-left k*k block D:

    A' = C + B^T D^{-1} B  (mod 2)

where M = [[D, B], [B^T, C]].  Admissibility requires det(D) != 0 mod 2.

The bracket [G] is the F_2 sum (symmetric difference by isomorphism class)
of all graphs H_{S,alpha} obtained from admissible pairs.

Notes
-----
Equivalence in the bracket definition is taken up to graph isomorphism here.
The stricter notion (equivalence under Reidemeister move II) is deferred to
future work.
"""

from __future__ import annotations

import itertools
import warnings
from collections.abc import Sequence

import networkx as nx
import numpy as np

from src.objects.graph_base import Node


def _f2_inverse(matrix: np.ndarray) -> np.ndarray | None:
    """Compute the inverse of a square matrix over F_2 via Gauss-Jordan.

    Parameters
    ----------
    matrix : np.ndarray
        Square integer array with entries in {0, 1}, interpreted as a matrix
        over the field F_2.

    Returns
    -------
    np.ndarray or None
        Inverse matrix over F_2, or None if the matrix is singular.
    """
    k = matrix.shape[0]
    if k == 0:
        return np.empty((0, 0), dtype=np.uint8)

    aug = np.hstack([matrix.astype(np.uint8), np.eye(k, dtype=np.uint8)])

    for col in range(k):
        pivot = None
        for row in range(col, k):
            if aug[row, col] == 1:
                pivot = row
                break
        if pivot is None:
            return None

        if pivot != col:
            aug[[col, pivot]] = aug[[pivot, col]]

        for row in range(k):
            if row != col and aug[row, col] == 1:
                aug[row] = (aug[row] + aug[col]) % 2

    return aug[:, k:]


def _schur_complement(A: np.ndarray, k: int, alpha: tuple[int, ...]) -> np.ndarray | None:
    """Compute the Schur complement block for a given alpha vector.

    Given the adjacency matrix A (with even-vertex rows/columns first),
    build M = A + diag(alpha, 0, ..., 0) and compute the Schur complement
    A' = C + B^T D^{-1} B over F_2, where D = M[:k, :k].

    Parameters
    ----------
    A : np.ndarray
        Full adjacency matrix of shape (n, n) with entries in {0, 1},
        even vertices occupying the first k rows and columns.
    k : int
        Number of even vertices (size of the top-left block).
    alpha : tuple[int, ...]
        Diagonal perturbation vector of length k with entries in {0, 1}.

    Returns
    -------
    np.ndarray or None
        The (n-k) x (n-k) Schur complement matrix over F_2, or None if
        the top-left block D is singular over F_2.
    """
    n = A.shape[0]
    M = A.copy().astype(np.uint8)
    for i in range(k):
        M[i, i] = (M[i, i] + alpha[i]) % 2

    D = M[:k, :k]
    B = M[:k, k:]
    C = M[k:, k:]

    D_inv = _f2_inverse(D)
    if D_inv is None:
        return None

    if k == 0:
        return C % 2

    A_prime = (C + B.T @ D_inv @ B) % 2
    return A_prime.astype(np.uint8)


def _graph_from_matrix(A_prime: np.ndarray) -> nx.Graph:
    """Build a networkx Graph from a symmetric adjacency matrix over F_2.

    Diagonal entries of A_prime are ignored: only off-diagonal entries
    contribute edges.  This corresponds to treating the Schur complement
    as a simple graph.

    Parameters
    ----------
    A_prime : np.ndarray
        Square integer array with entries in {0, 1} representing an adjacency
        matrix.  Diagonal entries are ignored.

    Returns
    -------
    nx.Graph
        Simple graph with integer node labels 0, 1, ..., m-1.
    """
    m = A_prime.shape[0]
    H = nx.Graph()
    H.add_nodes_from(range(m))
    for i in range(m):
        for j in range(i + 1, m):
            if A_prime[i, j] == 1:
                H.add_edge(i, j)
    return H


def _graph_signature(graph: nx.Graph) -> tuple[str, int, int]:
    """Return a fast structural signature for approximate isomorphism grouping.

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


def _apply_f2_arithmetic(graphs: list[nx.Graph]) -> list[nx.Graph]:
    """Apply F_2 arithmetic to a list of graphs, cancelling isomorphic pairs.

    Graphs that appear an even number of times (up to isomorphism) cancel out.
    One representative is returned for each isomorphism class with an odd count.

    Parameters
    ----------
    graphs : list[nx.Graph]
        Input list of graphs, possibly containing isomorphic duplicates.

    Returns
    -------
    list[nx.Graph]
        Representatives of isomorphism classes with odd multiplicity,
        sorted by (node count, edge count) for determinism.
    """
    if not graphs:
        return []

    # Group by fast signature, then verify isomorphism within each group.
    sig_to_reps: dict[tuple[str, int, int], list[tuple[int, nx.Graph]]] = {}
    for graph in graphs:
        sig = _graph_signature(graph)
        sig_to_reps.setdefault(sig, [])

        matched = False
        for idx, (count, rep) in enumerate(sig_to_reps[sig]):
            if nx.is_isomorphic(graph, rep):
                sig_to_reps[sig][idx] = ((count + 1) % 2, rep)
                matched = True
                break
        if not matched:
            sig_to_reps[sig].append((1, graph))

    survivors: list[nx.Graph] = []
    for entries in sig_to_reps.values():
        for count, rep in entries:
            if count == 1:
                survivors.append(rep)

    survivors.sort(key=lambda g: (g.number_of_nodes(), g.number_of_edges()))
    return survivors


def compute_parity_bracket(
    graph: nx.Graph,
    even_nodes: Sequence[Node],
) -> list[nx.Graph]:
    """Compute the parity bracket of a graph for a given even-vertex set.

    For each alpha in {0, 1}^k satisfying the admissibility criterion
    det(A(S) + diag(alpha)) != 0 mod 2, the Schur complement H_{S,alpha} is
    computed.  The bracket is the F_2 sum of all such H_{S,alpha}, meaning
    isomorphism classes with even multiplicity cancel.

    Parameters
    ----------
    graph : nx.Graph
        Input graph.  Node labels can be arbitrary hashable values.
    even_nodes : Sequence[Node]
        Ordered sequence of vertices designated as even (the set S).  Must be
        a subset of graph nodes.  The order determines the indexing of alpha.

    Returns
    -------
    list[nx.Graph]
        Representatives of the F_2 bracket summands that survive cancellation,
        each with integer node labels 0, 1, ..., m-1 where m = n - k.
        Empty list means the bracket is zero.

    Raises
    ------
    ValueError
        If any element of even_nodes is not a node of graph, or if
        even_nodes contains duplicates.
    """
    even_set = list(dict.fromkeys(even_nodes))  # deduplicate, preserve order
    if len(even_set) != len(even_nodes):
        raise ValueError('even_nodes contains duplicate entries.')
    graph_nodes = set(graph.nodes())
    missing = set(even_set) - graph_nodes
    if missing:
        raise ValueError(f'even_nodes contains nodes not in graph: {missing}')

    k = len(even_set)
    other_nodes = [v for v in graph.nodes() if v not in set(even_set)]
    all_nodes = list(even_set) + other_nodes
    n = len(all_nodes)

    node_to_idx = {v: i for i, v in enumerate(all_nodes)}
    A = np.zeros((n, n), dtype=np.uint8)
    for u, v in graph.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        A[i, j] = A[j, i] = 1

    terms: list[nx.Graph] = []
    for alpha in itertools.product((0, 1), repeat=k):
        A_prime = _schur_complement(A, k, alpha)
        if A_prime is None:
            continue
        H = _graph_from_matrix(A_prime)
        terms.append(H)

    return _apply_f2_arithmetic(terms)

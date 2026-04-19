"""Reidemeister move #2 for graph representations."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations

from src.objects.graph_base import Node

from ._common import (
    GraphInput,
    GraphOutput,
    as_networkx,
    to_output_type,
    validate_distinct_nodes,
)


def check_move_2_remove(graph: GraphInput, left: Node, right: Node) -> bool:
    """
    Check if move #2 remove can be applied to a node pair.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    left : Node
        First node of the pair.
    right : Node
        Second node of the pair.

    Returns
    -------
    bool
        True if nodes are distinct, present, and have identical adjacency in
        the remaining graph (excluding each other).
    """
    if left == right:
        return False

    nx_graph = as_networkx(graph)
    if left not in nx_graph or right not in nx_graph:
        return False

    left_neighbors = set(nx_graph.neighbors(left)) - {right}
    right_neighbors = set(nx_graph.neighbors(right)) - {left}
    return left_neighbors == right_neighbors


def apply_move_2_remove(graph: GraphInput, left: Node, right: Node) -> GraphOutput:
    """
    Remove a pair of nodes with identical remaining adjacency.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    left : Node
        First node of the pair.
    right : Node
        Second node of the pair.

    Returns
    -------
    GraphOutput
        New graph with two removed nodes.

    Raises
    ------
    ValueError
        If move #2 remove conditions are not satisfied.
    """
    if not check_move_2_remove(graph, left, right):
        raise ValueError("Move #2 remove requires a valid pair with equal remaining adjacency.")

    nx_graph = as_networkx(graph)
    updated = nx_graph.copy()
    updated.remove_nodes_from([left, right])
    return to_output_type(graph, updated)


def check_move_2_add(
    graph: GraphInput,
    left: Node,
    right: Node,
    neighbors: Iterable[Node],
) -> bool:
    """
    Check if move #2 add can be applied for a new node pair.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    left : Node
        New first node.
    right : Node
        New second node.
    neighbors : Iterable[Node]
        Shared neighbor set in the current graph.

    Returns
    -------
    bool
        True if pair can be added with the provided shared neighbors.
    """
    if left == right:
        return False

    nx_graph = as_networkx(graph)
    if left in nx_graph or right in nx_graph:
        return False

    neighbor_set = set(neighbors)
    if left in neighbor_set or right in neighbor_set:
        return False

    return neighbor_set.issubset(set(nx_graph.nodes))


def apply_move_2_add(
    graph: GraphInput,
    left: Node,
    right: Node,
    neighbors: Iterable[Node],
    connect_pair: bool,
) -> GraphOutput:
    """
    Add a node pair with identical shared neighbors.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    left : Node
        New first node.
    right : Node
        New second node.
    neighbors : Iterable[Node]
        Shared neighbor set in the current graph.
    connect_pair : bool
        Whether to connect the new pair with an edge.

    Returns
    -------
    GraphOutput
        New graph with added pair.

    Raises
    ------
    ValueError
        If move #2 add conditions are not satisfied.
    """
    if not check_move_2_add(graph, left, right, neighbors):
        raise ValueError("Move #2 add conditions are not satisfied.")

    validate_distinct_nodes(left, right)
    neighbor_set = set(neighbors)

    nx_graph = as_networkx(graph)
    updated = nx_graph.copy()
    updated.add_nodes_from([left, right])

    for node in neighbor_set:
        updated.add_edge(left, node)
        updated.add_edge(right, node)

    if connect_pair:
        updated.add_edge(left, right)

    return to_output_type(graph, updated)


def find_move_2_remove_candidates(graph: GraphInput) -> list[tuple[Node, Node]]:
    """
    Find all valid node pairs for move #2 remove.

    Parameters
    ----------
    graph : GraphInput
        Input graph.

    Returns
    -------
    list[tuple[Node, Node]]
        Node pairs satisfying move #2 remove conditions.
    """
    nx_graph = as_networkx(graph)
    nodes = list(nx_graph.nodes)
    candidates: list[tuple[Node, Node]] = []

    for left, right in combinations(nodes, 2):
        if check_move_2_remove(nx_graph, left, right):
            candidates.append((left, right))

    return candidates

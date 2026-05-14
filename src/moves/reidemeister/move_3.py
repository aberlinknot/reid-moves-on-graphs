"""Reidemeister move #3 for graph representations."""

from __future__ import annotations

from itertools import combinations

from src.objects.graph_base import Node

from ._common import GraphInput, GraphOutput, as_networkx, to_output_type, validate_distinct_nodes


def check_move_3(graph: GraphInput, first: Node, second: Node, third: Node) -> bool:
    """
    Check if move #3 can be applied to a triple.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    first : Node
        First node in triple.
    second : Node
        Second node in triple.
    third : Node
        Third node in triple.

    Returns
    -------
    bool
        True if nodes are distinct, present, and every other node is adjacent
        to exactly 0 or 2 nodes in the triple.
    """
    if len({first, second, third}) != 3:
        return False

    nx_graph = as_networkx(graph)
    triple = {first, second, third}
    if not triple.issubset(set(nx_graph.nodes)):
        return False

    for node in nx_graph.nodes:
        if node in triple:
            continue

        adjacent_count = sum(1 for triple_node in triple if nx_graph.has_edge(node, triple_node))
        if adjacent_count not in {0, 2}:
            return False

    return True


def apply_move_3(graph: GraphInput, first: Node, second: Node, third: Node) -> GraphOutput:
    """
    Apply move #3 as edge complement in a valid triple.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    first : Node
        First node in triple.
    second : Node
        Second node in triple.
    third : Node
        Third node in triple.

    Returns
    -------
    GraphOutput
        New graph with toggled edges in the triple.

    Raises
    ------
    ValueError
        If move #3 conditions are not satisfied.
    """
    validate_distinct_nodes(first, second, third)
    if not check_move_3(graph, first, second, third):
        raise ValueError("Move #3 conditions are not satisfied for the provided triple.")

    nx_graph = as_networkx(graph)
    updated = nx_graph.copy()

    for left, right in combinations([first, second, third], 2):
        if updated.has_edge(left, right):
            updated.remove_edge(left, right)
        else:
            updated.add_edge(left, right)

    return to_output_type(graph, updated)


def find_move_3_candidates(graph: GraphInput) -> list[tuple[Node, Node, Node]]:
    """
    Find all node triples valid for move #3.

    Parameters
    ----------
    graph : GraphInput
        Input graph.

    Returns
    -------
    list[tuple[Node, Node, Node]]
        Valid triples for move #3.
    """
    nx_graph = as_networkx(graph)
    nodes = list(nx_graph.nodes)
    candidates: list[tuple[Node, Node, Node]] = []

    for first, second, third in combinations(nodes, 3):
        if check_move_3(nx_graph, first, second, third):
            candidates.append((first, second, third))

    return candidates

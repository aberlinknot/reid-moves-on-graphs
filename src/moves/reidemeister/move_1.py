"""Reidemeister move #1 for graph representations."""

from __future__ import annotations

from collections.abc import Iterable

from src.objects.graph_base import Node

from ._common import GraphInput, GraphOutput, as_networkx, to_output_type


def check_move_1_remove(graph: GraphInput, node: Node) -> bool:
    """
    Check if move #1 remove can be applied to a node.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    node : Node
        Candidate node to remove.

    Returns
    -------
    bool
        True if node exists and is isolated, else False.
    """
    nx_graph = as_networkx(graph)
    return node in nx_graph and nx_graph.degree[node] == 0


def apply_move_1_remove(graph: GraphInput, node: Node) -> GraphOutput:
    """
    Remove an isolated node (decreasing variant of move #1).

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    node : Node
        Isolated node to remove.

    Returns
    -------
    GraphOutput
        New graph with removed isolated node.

    Raises
    ------
    ValueError
        If node is missing or not isolated.
    """
    if not check_move_1_remove(graph, node):
        raise ValueError("Move #1 remove requires an existing isolated node.")

    nx_graph = as_networkx(graph)
    updated = nx_graph.copy()
    updated.remove_node(node)
    return to_output_type(graph, updated)


def check_move_1_add(graph: GraphInput, node: Node) -> bool:
    """
    Check if move #1 add can be applied for a node label.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    node : Node
        New node label.

    Returns
    -------
    bool
        True if label is not present in graph, else False.
    """
    return node not in as_networkx(graph)


def apply_move_1_add(graph: GraphInput, node: Node) -> GraphOutput:
    """
    Add a new isolated node (increasing variant of move #1).

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    node : Node
        New isolated node.

    Returns
    -------
    GraphOutput
        New graph with the added isolated node.

    Raises
    ------
    ValueError
        If node label already exists.
    """
    if not check_move_1_add(graph, node):
        raise ValueError("Move #1 add requires a node label not present in graph.")

    nx_graph = as_networkx(graph)
    updated = nx_graph.copy()
    updated.add_node(node)
    return to_output_type(graph, updated)


def find_move_1_remove_candidates(graph: GraphInput) -> list[Node]:
    """
    Find nodes eligible for move #1 remove.

    Parameters
    ----------
    graph : GraphInput
        Input graph.

    Returns
    -------
    list[Node]
        Isolated nodes.
    """
    nx_graph = as_networkx(graph)
    return [node for node, degree in nx_graph.degree if degree == 0]


def find_move_1_add_candidates(graph: GraphInput, labels: Iterable[Node]) -> list[Node]:
    """
    Filter candidate labels that can be used for move #1 add.

    Parameters
    ----------
    graph : GraphInput
        Input graph.
    labels : Iterable[Node]
        Candidate labels provided by caller.

    Returns
    -------
    list[Node]
        Labels that are not present in graph.
    """
    return [label for label in labels if check_move_1_add(graph, label)]

"""Shared helpers for Reidemeister moves on graphs."""

from __future__ import annotations

import networkx as nx

from src.objects.graph_base import BaseGraph, Node

type GraphInput = nx.Graph | BaseGraph
type GraphOutput = nx.Graph | BaseGraph


def as_networkx(graph: GraphInput) -> nx.Graph:
    """
    Convert input graph to networkx.Graph reference.

    Parameters
    ----------
    graph : GraphInput
        Input graph as networkx.Graph or BaseGraph.

    Returns
    -------
    nx.Graph
        Underlying networkx graph reference.
    """
    if isinstance(graph, BaseGraph):
        return graph.to_networkx()
    return graph


def to_output_type(source: GraphInput, updated_graph: nx.Graph) -> GraphOutput:
    """
    Convert updated networkx graph back to source graph type.

    Parameters
    ----------
    source : GraphInput
        Original graph object.
    updated_graph : nx.Graph
        Updated graph copy.

    Returns
    -------
    GraphOutput
        nx.Graph for nx.Graph input, BaseGraph for BaseGraph input.
    """
    if isinstance(source, BaseGraph):
        return source.__class__.from_networkx(updated_graph)
    return updated_graph


def validate_distinct_nodes(*nodes: Node) -> None:
    """Validate that nodes are pairwise distinct."""
    if len(set(nodes)) != len(nodes):
        raise ValueError("All provided nodes must be distinct.")

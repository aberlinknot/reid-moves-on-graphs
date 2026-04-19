"""
Strict parser for graph YAML configuration files.

All code, comments, and docstrings must be in English (NumPy style).
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import yaml


Node = Hashable
Edge = tuple[Node, Node]


@dataclass(frozen=True)
class GraphConfig:
    """
    Parsed graph configuration.

    Parameters
    ----------
    name : str
        Graph preset name.
    title : str
        Graph title for plotting.
    with_labels : bool
        Whether labels should be shown when plotting.
    nodes : list[Node]
        Node sequence.
    edges : list[Edge]
        Edge list as node pairs.
    """

    name: str
    title: str
    with_labels: bool
    nodes: list[Node]
    edges: list[Edge]


def load_yaml_mapping(path: Path) -> dict[str, object]:
    """
    Load YAML file and validate mapping root.

    Parameters
    ----------
    path : Path
        Path to YAML file.

    Returns
    -------
    dict[str, object]
        Parsed mapping.

    Raises
    ------
    ValueError
        If YAML root is not a mapping.
    """
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError(f"{path}: root must be a mapping.")

    return raw


def parse_graph_yaml(path: Path) -> GraphConfig:
    """
    Parse one graph YAML file into a validated GraphConfig.

    Parameters
    ----------
    path : Path
        Path to YAML file.

    Returns
    -------
    GraphConfig
        Validated graph configuration.

    Raises
    ------
    ValueError
        If the YAML structure is invalid.
    """
    raw = load_yaml_mapping(path)

    name_raw = raw.get("name", path.stem)
    if not isinstance(name_raw, str) or not name_raw:
        raise ValueError(f"{path}: 'name' must be a non-empty string.")

    title_raw = raw.get("title", name_raw)
    if not isinstance(title_raw, str):
        raise ValueError(f"{path}: 'title' must be a string.")

    with_labels_raw = raw.get("with_labels", True)
    if not isinstance(with_labels_raw, bool):
        raise ValueError(f"{path}: 'with_labels' must be a boolean.")

    nodes_raw = raw.get("nodes", [])
    if not isinstance(nodes_raw, list):
        raise ValueError(f"{path}: 'nodes' must be a list.")
    nodes = _validate_nodes(nodes_raw, path)

    edges_raw = raw.get("edges")
    if not isinstance(edges_raw, list):
        raise ValueError(f"{path}: 'edges' must be a list.")
    edges = _validate_edges(edges_raw, path)

    return GraphConfig(
        name=name_raw,
        title=title_raw,
        with_labels=with_labels_raw,
        nodes=nodes,
        edges=edges,
    )


def build_graph(config: GraphConfig) -> nx.Graph:
    """
    Build a networkx graph from GraphConfig.

    Parameters
    ----------
    config : GraphConfig
        Parsed graph configuration.

    Returns
    -------
    nx.Graph
        Constructed graph.
    """
    graph = nx.Graph()
    graph.add_nodes_from(config.nodes)
    graph.add_edges_from(config.edges)
    return graph


def list_graph_configs(graphs_dir: Path) -> list[Path]:
    """
    List YAML graph config files from a directory.

    Parameters
    ----------
    graphs_dir : Path
        Directory containing YAML files.

    Returns
    -------
    list[Path]
        Sorted list of YAML file paths.
    """
    return sorted(
        [p for p in graphs_dir.iterdir() if p.is_file() and p.suffix in {".yaml", ".yml"}]
    )


def _validate_nodes(raw_nodes: list[object], path: Path) -> list[Node]:
    nodes: list[Node] = []
    for node in raw_nodes:
        if not isinstance(node, Hashable):
            raise ValueError(f"{path}: node '{node}' is not hashable.")
        nodes.append(node)
    return nodes


def _validate_edges(raw_edges: list[object], path: Path) -> list[Edge]:
    edges: list[Edge] = []
    for edge in raw_edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError(f"{path}: each edge must be a list with exactly two items.")

        left, right = edge[0], edge[1]
        if not isinstance(left, Hashable) or not isinstance(right, Hashable):
            raise ValueError(f"{path}: edge '{edge}' contains non-hashable node.")

        edges.append((left, right))

    return edges

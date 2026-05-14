"""Shared helpers for random-move runs and atlas scans."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import networkx as nx

from src.moves.reidemeister import (
    apply_move_1_add,
    apply_move_1_remove,
    apply_move_2_add,
    apply_move_2_remove,
    apply_move_3,
    find_move_1_remove_candidates,
    find_move_2_remove_candidates,
    find_move_3_candidates,
)
from src.parsers.graph_yaml_parser import Edge, build_graph, load_yaml_mapping, parse_graph_yaml

MoveName = Literal["move_1_add", "move_1_remove", "move_2_add", "move_2_remove", "move_3"]
SourceType = Literal["yaml", "manual", "atlas"]
RunRecordWriter = Callable[[dict[str, object]], None]


@dataclass(frozen=True)
class RunConfig:
    """Configuration for a single weighted random-move run."""

    iterations: int
    seed: int | None
    log_path: Path
    source: dict[str, object]
    weights: dict[MoveName, float]


@dataclass(frozen=True)
class AtlasScanConfig:
    """Configuration for a batch atlas scan."""

    iterations: int
    seed: int | None
    log_path: Path
    weights: dict[MoveName, float]
    node_count: int | None
    limit: int | None


def parse_move_weights(
    weights_raw: object, required_moves: tuple[MoveName, ...]
) -> dict[MoveName, float]:
    """Validate and normalize move weights from a YAML mapping."""
    if not isinstance(weights_raw, dict):
        raise ValueError("Config must contain mapping 'weights'.")

    weights: dict[MoveName, float] = {}
    for move in required_moves:
        value = weights_raw.get(move)
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Weight for '{move}' must be non-negative numeric value.")
        weights[move] = float(value)

    if sum(weights.values()) <= 0:
        raise ValueError("Sum of weights must be positive.")

    return weights


def parse_run_config(path: Path) -> RunConfig:
    """Parse a single-run configuration from YAML."""
    raw = load_yaml_mapping(path)

    iterations = raw.get("iterations", 100)
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("'iterations' must be a positive integer.")

    seed_raw = raw.get("seed", None)
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise ValueError("'seed' must be an integer or null.")

    log_path_raw = raw.get("log_path", "scripts/random_moves/single_run/logs/random_moves.jsonl")
    if not isinstance(log_path_raw, str) or not log_path_raw:
        raise ValueError("'log_path' must be a non-empty string.")
    log_path = Path(log_path_raw)

    source_raw = raw.get("source")
    if not isinstance(source_raw, dict):
        raise ValueError("'source' must be a mapping.")

    required_moves: tuple[MoveName, ...] = (
        "move_1_add",
        "move_1_remove",
        "move_2_add",
        "move_2_remove",
        "move_3",
    )
    weights = parse_move_weights(raw.get("weights"), required_moves)

    return RunConfig(
        iterations=iterations,
        seed=seed_raw,
        log_path=log_path,
        source=source_raw,
        weights=weights,
    )


def parse_atlas_scan_config(path: Path) -> AtlasScanConfig:
    """Parse a batch atlas-scan configuration from YAML."""
    raw = load_yaml_mapping(path)

    iterations = raw.get("iterations", 1000)
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("'iterations' must be a positive integer.")

    seed_raw = raw.get("seed", None)
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise ValueError("'seed' must be an integer or null.")

    log_path_raw = raw.get(
        "log_path", "scripts/random_moves/atlas_run/logs/random_moves_atlas_scan.jsonl"
    )
    if not isinstance(log_path_raw, str) or not log_path_raw:
        raise ValueError("'log_path' must be a non-empty string.")
    log_path = Path(log_path_raw)

    required_moves: tuple[MoveName, ...] = (
        "move_1_add",
        "move_1_remove",
        "move_2_add",
        "move_2_remove",
        "move_3",
    )
    weights = parse_move_weights(raw.get("weights"), required_moves)

    scan_raw = raw.get("scan", {})
    if not isinstance(scan_raw, dict):
        raise ValueError("'scan' must be a mapping when provided.")

    node_count_raw = scan_raw.get("node_count")
    if node_count_raw is not None and not isinstance(node_count_raw, int):
        raise ValueError("'scan.node_count' must be an integer or null.")
    if isinstance(node_count_raw, int) and node_count_raw <= 0:
        raise ValueError("'scan.node_count' must be positive when provided.")

    limit_raw = scan_raw.get("limit")
    if limit_raw is not None and not isinstance(limit_raw, int):
        raise ValueError("'scan.limit' must be an integer or null.")
    if isinstance(limit_raw, int) and limit_raw <= 0:
        raise ValueError("'scan.limit' must be positive when provided.")

    return AtlasScanConfig(
        iterations=iterations,
        seed=seed_raw,
        log_path=log_path,
        weights=weights,
        node_count=node_count_raw,
        limit=limit_raw,
    )


def load_initial_graph(source_cfg: dict[str, object]) -> tuple[nx.Graph, str]:
    """Load an initial graph from YAML, manual, or atlas source configuration."""
    source_type_raw = source_cfg.get("type")
    if source_type_raw not in {"yaml", "manual", "atlas"}:
        raise ValueError("Source type must be one of: yaml, manual, atlas.")

    source_type = source_type_raw
    if source_type == "yaml":
        yaml_path = source_cfg.get("yaml_path")
        if not isinstance(yaml_path, str) or not yaml_path:
            raise ValueError("For yaml source provide non-empty 'yaml_path'.")

        graph_config = parse_graph_yaml(Path(yaml_path))
        return build_graph(graph_config), f"yaml:{yaml_path}"

    if source_type == "manual":
        manual_raw = source_cfg.get("manual")
        if not isinstance(manual_raw, dict):
            raise ValueError("For manual source provide mapping 'manual'.")

        graph = nx.Graph()

        nodes_raw = manual_raw.get("nodes", [])
        if not isinstance(nodes_raw, list):
            raise ValueError("manual.nodes must be a list.")
        graph.add_nodes_from(nodes_raw)

        edges_raw = manual_raw.get("edges", [])
        if not isinstance(edges_raw, list):
            raise ValueError("manual.edges must be a list.")

        edges: list[Edge] = []
        for edge in edges_raw:
            if not isinstance(edge, list) or len(edge) != 2:
                raise ValueError("Each manual edge must contain exactly two nodes.")
            edges.append((edge[0], edge[1]))

        graph.add_edges_from(edges)
        return graph, "manual"

    atlas_index_raw = source_cfg.get("atlas_index")
    if not isinstance(atlas_index_raw, int) or atlas_index_raw < 0:
        raise ValueError("For atlas source provide non-negative integer 'atlas_index'.")

    atlas_graphs = list(nx.graph_atlas_g())
    if atlas_index_raw >= len(atlas_graphs):
        raise ValueError(f"atlas_index={atlas_index_raw} is out of range for graph_atlas_g().")

    return atlas_graphs[atlas_index_raw].copy(), f"atlas:{atlas_index_raw}"


def choose_weighted_move(rng: random.Random, weights: dict[MoveName, float]) -> MoveName:
    """Choose one move name according to configured weights."""
    moves = list(weights.keys())
    move_weights = [weights[move] for move in moves]
    return rng.choices(moves, weights=move_weights, k=1)[0]


def next_numeric_label(graph: nx.Graph) -> int:
    """Generate the next free numeric node label."""
    numeric_nodes = [node for node in graph.nodes if isinstance(node, int)]
    candidate = max(numeric_nodes) + 1 if numeric_nodes else 0
    while candidate in graph:
        candidate += 1
    return candidate


def serialize_node(node: object) -> object:
    """Serialize a node into a JSON-friendly value."""
    if isinstance(node, (str, int, float, bool)) or node is None:
        return node
    return repr(node)


def snapshot_graph(graph: nx.Graph) -> dict[str, object]:
    """Create a compact graph snapshot for logging."""
    return {
        "nodes": [serialize_node(node) for node in graph.nodes],
        "edges": [[serialize_node(left), serialize_node(right)] for left, right in graph.edges],
    }


def apply_random_move(
    rng: random.Random, graph: nx.Graph, move: MoveName
) -> tuple[nx.Graph, bool, list[object] | None]:
    """Apply one randomly instantiated move variant."""
    if move == "move_1_add":
        node = next_numeric_label(graph)
        updated = apply_move_1_add(graph, node)
        return updated, True, [serialize_node(node)]

    if move == "move_1_remove":
        candidates = find_move_1_remove_candidates(graph)
        if not candidates:
            return graph, False, None
        node = rng.choice(candidates)
        updated = apply_move_1_remove(graph, node)
        return updated, True, [serialize_node(node)]

    if move == "move_2_add":
        left = next_numeric_label(graph)
        right = left + 1
        while right in graph:
            right += 1

        neighbors = [node for node in graph.nodes if rng.random() < 0.5]
        connect_pair = rng.random() < 0.5

        updated = apply_move_2_add(
            graph,
            left=left,
            right=right,
            neighbors=neighbors,
            connect_pair=connect_pair,
        )
        return updated, True, [serialize_node(left), serialize_node(right)]

    if move == "move_2_remove":
        candidates = find_move_2_remove_candidates(graph)
        if not candidates:
            return graph, False, None
        left, right = rng.choice(candidates)
        updated = apply_move_2_remove(graph, left, right)
        return updated, True, [serialize_node(left), serialize_node(right)]

    candidates = find_move_3_candidates(graph)
    if not candidates:
        return graph, False, None

    first, second, third = rng.choice(candidates)
    updated = apply_move_3(graph, first, second, third)
    return updated, True, [serialize_node(first), serialize_node(second), serialize_node(third)]


def run_random_walk(
    graph: nx.Graph,
    iterations: int,
    weights: dict[MoveName, float],
    seed: int | None,
    *,
    run_id: str,
    source_name: str,
    stop_on_extinction: bool,
    on_record: RunRecordWriter,
    extra_fields: dict[str, object] | None = None,
) -> dict[str, object]:
    """Run a weighted random walk and stream JSON-serializable records."""
    graph_state = graph.copy()
    rng = random.Random(seed)
    start_nodes = graph_state.number_of_nodes()
    start_edges = graph_state.number_of_edges()
    run_fields = {
        "run_id": run_id,
        "source": source_name,
    }
    if extra_fields:
        run_fields.update(extra_fields)

    on_record(
        {
            "event": "run_start",
            **run_fields,
            "iterations": iterations,
            "seed": seed,
            "weights": weights,
            "start_nodes": start_nodes,
            "start_edges": start_edges,
        }
    )

    applied_moves = 0
    reached_extinction = start_nodes <= 1
    extinct_iteration: int | None = 0 if reached_extinction else None

    for iteration in range(1, iterations + 1):
        move = choose_weighted_move(rng, weights)
        current_snapshot = snapshot_graph(graph_state)

        updated_graph, applied, applied_to = apply_random_move(rng, graph_state, move)
        graph_state = updated_graph

        if applied:
            applied_moves += 1

        on_record(
            {
                "event": "iteration",
                **run_fields,
                "iteration": iteration,
                "current_graph_nodes": current_snapshot["nodes"],
                "current_graph_edges": current_snapshot["edges"],
                "selected_move": move,
                "applied": applied,
                "applied_to": applied_to,
                "result_node_count": graph_state.number_of_nodes(),
                "result_nodes": [serialize_node(node) for node in graph_state.nodes],
            }
        )

        if stop_on_extinction and graph_state.number_of_nodes() <= 1:
            reached_extinction = True
            extinct_iteration = iteration
            break

    summary = {
        "event": "run_end",
        **run_fields,
        "applied_moves": applied_moves,
        "final_nodes": graph_state.number_of_nodes(),
        "final_edges": graph_state.number_of_edges(),
        "reached_extinction": reached_extinction,
        "extinct_iteration": extinct_iteration,
        "iterations_budget": iterations,
    }
    on_record(summary)
    return summary


def iter_atlas_graphs(
    *,
    node_count: int | None = None,
    limit: int | None = None,
) -> list[tuple[int, nx.Graph]]:
    """Collect atlas graphs matching the requested filter."""
    indexed_graphs = [
        (index, graph.copy())
        for index, graph in enumerate(nx.graph_atlas_g())
        if node_count is None or graph.number_of_nodes() == node_count
    ]
    indexed_graphs.sort(
        key=lambda pair: (pair[1].number_of_nodes(), pair[1].number_of_edges(), pair[0])
    )

    if limit is not None:
        indexed_graphs = indexed_graphs[:limit]

    return indexed_graphs


def dumps_record(record: dict[str, object]) -> str:
    """Serialize a log record as one JSON line."""
    return json.dumps(record, ensure_ascii=False)

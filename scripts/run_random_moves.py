"""Run long random sequences of Reidemeister moves with weighted probabilities."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


@dataclass(frozen=True)
class RunConfig:
    """Configuration for weighted random-moves run."""

    iterations: int
    seed: int | None
    log_path: Path
    source: dict[str, object]
    weights: dict[MoveName, float]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run weighted random Reidemeister moves.")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to run YAML config.",
    )
    return parser.parse_args()


def parse_run_config(path: Path) -> RunConfig:
    """Parse and validate run configuration from YAML mapping."""
    raw = load_yaml_mapping(path)

    iterations = raw.get("iterations", 100)
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("'iterations' must be a positive integer.")

    seed_raw = raw.get("seed", None)
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise ValueError("'seed' must be an integer or null.")
    seed = seed_raw

    log_path_raw = raw.get("log_path", "results/logs/random_moves.jsonl")
    if not isinstance(log_path_raw, str) or not log_path_raw:
        raise ValueError("'log_path' must be a non-empty string.")
    log_path = Path(log_path_raw)

    source_raw = raw.get("source")
    if not isinstance(source_raw, dict):
        raise ValueError("'source' must be a mapping.")

    weights_raw = raw.get("weights")
    if not isinstance(weights_raw, dict):
        raise ValueError("'weights' must be a mapping.")

    required_moves: tuple[MoveName, ...] = (
        "move_1_add",
        "move_1_remove",
        "move_2_add",
        "move_2_remove",
        "move_3",
    )

    weights: dict[MoveName, float] = {}
    for move in required_moves:
        value = weights_raw.get(move)
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Weight for '{move}' must be non-negative numeric value.")
        weights[move] = float(value)

    if sum(weights.values()) <= 0:
        raise ValueError("Sum of weights must be positive.")

    return RunConfig(
        iterations=iterations,
        seed=seed,
        log_path=log_path,
        source=source_raw,
        weights=weights,
    )


def load_initial_graph(source_cfg: dict[str, object]) -> tuple[nx.Graph, str]:
    """Load initial graph from yaml/manual/atlas source config."""
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

    atlas = nx.graph_atlas(atlas_index_raw)
    if atlas_index_raw >= len(atlas):
        raise ValueError(f"atlas_index={atlas_index_raw} is out of range for graph_atlas().")

    return atlas[atlas_index_raw].copy(), f"atlas:{atlas_index_raw}"


def choose_weighted_move(rng: random.Random, weights: dict[MoveName, float]) -> MoveName:
    """Choose one move name according to configured weights."""
    moves = list(weights.keys())
    move_weights = [weights[move] for move in moves]
    return rng.choices(moves, weights=move_weights, k=1)[0]


def next_numeric_label(graph: nx.Graph) -> int:
    """Generate next free numeric node label."""
    numeric_nodes = [node for node in graph.nodes if isinstance(node, int)]
    candidate = max(numeric_nodes) + 1 if numeric_nodes else 0
    while candidate in graph:
        candidate += 1
    return candidate


def serialize_node(node: object) -> object:
    """Serialize node for compact JSON logging."""
    if isinstance(node, (str, int, float, bool)) or node is None:
        return node
    return repr(node)


def snapshot_graph(graph: nx.Graph) -> dict[str, object]:
    """Create compact graph snapshot without sorting for speed."""
    return {
        "nodes": [serialize_node(node) for node in graph.nodes],
        "edges": [[serialize_node(left), serialize_node(right)] for left, right in graph.edges],
    }


def apply_random_move(
    rng: random.Random, graph: nx.Graph, move: MoveName
) -> tuple[nx.Graph, bool, list[object] | None]:
    """Apply one randomly-instantiated move variant."""
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


def run(config: RunConfig) -> None:
    """Run weighted random-move loop and write compact JSONL log."""
    rng = random.Random(config.seed)
    graph, source_name = load_initial_graph(config.source)

    config.log_path.parent.mkdir(parents=True, exist_ok=True)
    with config.log_path.open("w", encoding="utf-8") as log_file:
        header = {
            "event": "run_start",
            "iterations": config.iterations,
            "seed": config.seed,
            "source": source_name,
            "weights": config.weights,
        }
        log_file.write(json.dumps(header, ensure_ascii=False) + "\n")

        for iteration in range(1, config.iterations + 1):
            move = choose_weighted_move(rng, config.weights)
            current_snapshot = snapshot_graph(graph)

            updated_graph, applied, applied_to = apply_random_move(rng, graph, move)
            graph = updated_graph

            record = {
                "iteration": iteration,
                "current_graph_nodes": current_snapshot["nodes"],
                "current_graph_edges": current_snapshot["edges"],
                "selected_move": move,
                "applied": applied,
                "applied_to": applied_to,
                "result_node_count": graph.number_of_nodes(),
                "result_nodes": [serialize_node(node) for node in graph.nodes],
            }
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Run completed. Log written to: {config.log_path}")


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    config = parse_run_config(args.config)
    run(config)


if __name__ == "__main__":
    main()

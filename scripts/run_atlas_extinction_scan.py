"""Scan NetworkX atlas graphs and detect extinction under weighted random Reidemeister walk."""

from __future__ import annotations

import argparse
import json
import random
import sys
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
from src.parsers.graph_yaml_parser import load_yaml_mapping


MoveName = Literal["move_1_add", "move_1_remove", "move_2_add", "move_2_remove", "move_3"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run weighted random walk on all atlas graphs and log extinction events."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("examples/run_configs/random_moves_path_6.yaml"),
        help="Path to run config used only for move weights and base seed.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Maximum number of random-walk iterations per atlas graph.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("results/logs/atlas_extinction_scan.jsonl"),
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of atlas graphs for quick smoke runs.",
    )
    return parser.parse_args()


def load_weights_and_seed(config_path: Path) -> tuple[dict[MoveName, float], int | None]:
    """Load move weights and optional seed from run config."""
    raw = load_yaml_mapping(config_path)

    weights_raw = raw.get("weights")
    if not isinstance(weights_raw, dict):
        raise ValueError("Config must contain mapping 'weights'.")

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

    seed_raw = raw.get("seed")
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise ValueError("'seed' must be an integer or null.")

    return weights, seed_raw


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


def apply_random_move(rng: random.Random, graph: nx.Graph, move: MoveName) -> tuple[nx.Graph, bool]:
    """Apply one randomly-instantiated move variant to the graph."""
    if move == "move_1_add":
        node = next_numeric_label(graph)
        return apply_move_1_add(graph, node), True

    if move == "move_1_remove":
        candidates = find_move_1_remove_candidates(graph)
        if not candidates:
            return graph, False
        node = rng.choice(candidates)
        return apply_move_1_remove(graph, node), True

    if move == "move_2_add":
        left = next_numeric_label(graph)
        right = left + 1
        while right in graph:
            right += 1

        neighbors = [node for node in graph.nodes if rng.random() < 0.5]
        connect_pair = rng.random() < 0.5

        return (
            apply_move_2_add(
                graph,
                left=left,
                right=right,
                neighbors=neighbors,
                connect_pair=connect_pair,
            ),
            True,
        )

    if move == "move_2_remove":
        candidates = find_move_2_remove_candidates(graph)
        if not candidates:
            return graph, False
        left, right = rng.choice(candidates)
        return apply_move_2_remove(graph, left, right), True

    candidates = find_move_3_candidates(graph)
    if not candidates:
        return graph, False

    first, second, third = rng.choice(candidates)
    return apply_move_3(graph, first, second, third), True


def run_single_graph(
    atlas_index: int,
    graph: nx.Graph,
    iterations: int,
    weights: dict[MoveName, float],
    seed: int | None,
) -> dict[str, object]:
    """Run random walk for one graph and return summary record."""
    graph_state = graph.copy()
    start_nodes = graph_state.number_of_nodes()
    start_edges = graph_state.number_of_edges()

    graph_seed = atlas_index if seed is None else seed + atlas_index
    rng = random.Random(graph_seed)

    success = start_nodes <= 1
    stop_iteration = 0 if success else None
    applied_moves = 0

    if not success:
        for iteration in range(1, iterations + 1):
            move = choose_weighted_move(rng, weights)
            updated, applied = apply_random_move(rng, graph_state, move)
            graph_state = updated
            if applied:
                applied_moves += 1

            if graph_state.number_of_nodes() <= 1:
                success = True
                stop_iteration = iteration
                break

    return {
        "atlas_index": atlas_index,
        "start_nodes": start_nodes,
        "start_edges": start_edges,
        "success": success,
        "stop_iteration": stop_iteration,
        "final_nodes": graph_state.number_of_nodes(),
        "final_edges": graph_state.number_of_edges(),
        "applied_moves": applied_moves,
        "iterations_budget": iterations,
        "seed": graph_seed,
    }


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if args.iterations <= 0:
        raise ValueError("--iterations must be positive.")

    weights, base_seed = load_weights_and_seed(args.config)

    atlas_graphs = list(nx.graph_atlas_g())
    indexed_graphs = list(enumerate(atlas_graphs))
    indexed_graphs.sort(
        key=lambda pair: (
            pair[1].number_of_nodes(),
            pair[1].number_of_edges(),
            pair[0],
        )
    )

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be positive.")
        indexed_graphs = indexed_graphs[: args.limit]

    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", encoding="utf-8") as log_file:
        header = {
            "event": "atlas_scan_start",
            "config": str(args.config),
            "iterations": args.iterations,
            "weights": weights,
            "base_seed": base_seed,
            "graphs_count": len(indexed_graphs),
        }
        log_file.write(json.dumps(header, ensure_ascii=False) + "\n")

        success_count = 0
        for atlas_index, graph in indexed_graphs:
            record = run_single_graph(
                atlas_index=atlas_index,
                graph=graph,
                iterations=args.iterations,
                weights=weights,
                seed=base_seed,
            )
            if record["success"]:
                success_count += 1

            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Scan completed. Graphs processed: {len(indexed_graphs)}")
    print(f"Success count (reached <=1 node): {success_count}")
    print(f"Log written to: {args.log}")


if __name__ == "__main__":
    main()

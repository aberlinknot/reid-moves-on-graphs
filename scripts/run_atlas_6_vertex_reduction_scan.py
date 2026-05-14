"""Scan 6-vertex atlas graphs with reduction-only weighted random Reidemeister walk."""

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
    apply_move_1_remove,
    apply_move_2_remove,
    apply_move_3,
    find_move_1_remove_candidates,
    find_move_2_remove_candidates,
    find_move_3_candidates,
)
from src.parsers.graph_yaml_parser import load_yaml_mapping

MoveName = Literal["move_1_remove", "move_2_remove", "move_3"]


DEFAULT_LOG = Path("results/logs/atlas_extinction_scan_6_vertices.jsonl")
DEFAULT_CONFIG = Path("examples/run_configs/random_moves_path_6.yaml")
DEFAULT_ITERATIONS = 10000


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run reduction-only random walk on all 6-vertex atlas graphs."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to run config used as source of base seed and reducing weights.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Maximum number of random-walk iterations per graph.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of 6-vertex graphs for smoke runs.",
    )
    return parser.parse_args()


def load_weights_and_seed(config_path: Path) -> tuple[dict[MoveName, float], int | None]:
    """Load reducing weights and seed from base run config.

    Increasing move weights are intentionally forced to zero by excluding them
    from the returned distribution.
    """
    raw = load_yaml_mapping(config_path)

    weights_raw = raw.get("weights")
    if not isinstance(weights_raw, dict):
        raise ValueError("Config must contain mapping 'weights'.")

    reducing_moves: tuple[MoveName, ...] = ("move_1_remove", "move_2_remove", "move_3")
    weights: dict[MoveName, float] = {}
    for move in reducing_moves:
        value = weights_raw.get(move)
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Weight for '{move}' must be non-negative numeric value.")
        weights[move] = float(value)

    if sum(weights.values()) <= 0:
        raise ValueError("Sum of reducing weights must be positive.")

    seed_raw = raw.get("seed")
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise ValueError("'seed' must be an integer or null.")

    return weights, seed_raw


def choose_weighted_move(rng: random.Random, weights: dict[MoveName, float]) -> MoveName:
    """Choose one reducing move name according to configured weights."""
    moves = list(weights.keys())
    move_weights = [weights[move] for move in moves]
    return rng.choices(moves, weights=move_weights, k=1)[0]


def apply_random_move(rng: random.Random, graph: nx.Graph, move: MoveName) -> tuple[nx.Graph, bool]:
    """Apply one randomly-instantiated reducing move variant to the graph."""
    if move == "move_1_remove":
        candidates = find_move_1_remove_candidates(graph)
        if not candidates:
            return graph, False
        node = rng.choice(candidates)
        return apply_move_1_remove(graph, node), True

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
    """Run reduction-only random walk for one 6-vertex atlas graph."""
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
        "weights": {
            "move_1_add": 0.0,
            "move_1_remove": weights["move_1_remove"],
            "move_2_add": 0.0,
            "move_2_remove": weights["move_2_remove"],
            "move_3": weights["move_3"],
        },
    }


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if args.iterations <= 0:
        raise ValueError("--iterations must be positive.")

    weights, base_seed = load_weights_and_seed(args.config)

    indexed_graphs = [
        (index, graph.copy())
        for index, graph in enumerate(nx.graph_atlas_g())
        if graph.number_of_nodes() == 6
    ]
    indexed_graphs.sort(key=lambda pair: (pair[1].number_of_edges(), pair[0]))

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be positive.")
        indexed_graphs = indexed_graphs[: args.limit]

    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", encoding="utf-8") as log_file:
        header = {
            "event": "atlas_6_vertex_reduction_scan_start",
            "config": str(args.config),
            "iterations": args.iterations,
            "base_seed": base_seed,
            "graphs_count": len(indexed_graphs),
            "weights": {
                "move_1_add": 0.0,
                "move_1_remove": weights["move_1_remove"],
                "move_2_add": 0.0,
                "move_2_remove": weights["move_2_remove"],
                "move_3": weights["move_3"],
            },
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

    print(f"Scan completed. 6-vertex graphs processed: {len(indexed_graphs)}")
    print(f"Success count (reached <=1 node): {success_count}")
    print(f"Log written to: {args.log}")


if __name__ == "__main__":
    main()

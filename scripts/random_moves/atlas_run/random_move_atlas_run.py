"""Scan atlas graphs with weighted random Reidemeister walks."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.logging_config import log_event, setup_logging

from ..random_move_run_core import (
    dumps_record,
    iter_atlas_graphs,
    parse_atlas_scan_config,
    run_random_walk,
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run weighted random walks on atlas graphs and log each run as a section."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to atlas scan YAML config.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging to see all graphs.",
    )
    return parser.parse_args()


def run(config_path: Path) -> None:
    """Run the atlas scan and write JSONL log records."""
    config = parse_atlas_scan_config(config_path)
    indexed_graphs = iter_atlas_graphs(node_count=config.node_count, limit=config.limit)
    scan_id = config.log_path.stem

    log_event(
        logger,
        logging.INFO,
        f"Starting atlas scan: {scan_id}. Graphs to process: {len(indexed_graphs)}",
        event="scan_start",
    )

    config.log_path.parent.mkdir(parents=True, exist_ok=True)
    with config.log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(
            dumps_record(
                {
                    "event": "scan_start",
                    "scan_id": scan_id,
                    "config": str(config_path),
                    "iterations": config.iterations,
                    "seed": config.seed,
                    "weights": config.weights,
                    "node_count": config.node_count,
                    "limit": config.limit,
                    "graphs_count": len(indexed_graphs),
                }
            )
            + "\n"
        )

        success_count = 0
        for graph_num, (atlas_index, graph) in enumerate(indexed_graphs, 1):
            run_id = f"atlas:{atlas_index}"

            # Log progress
            log_event(
                logger,
                logging.DEBUG,
                f"Processing graph {graph_num}/{len(indexed_graphs)}: atlas_index={atlas_index}, "
                f"nodes={graph.number_of_nodes()}, edges={graph.number_of_edges()}",
                event="graph_start",
                run_id=run_id,
                extra_fields={"graph_num": graph_num, "total_graphs": len(indexed_graphs)},
            )

            summary = run_random_walk(
                graph=graph,
                iterations=config.iterations,
                weights=config.weights,
                seed=None if config.seed is None else config.seed + atlas_index,
                run_id=run_id,
                source_name=run_id,
                stop_on_extinction=True,
                extra_fields={
                    "scan_id": scan_id,
                    "atlas_index": atlas_index,
                },
                on_record=lambda record: log_file.write(dumps_record(record) + "\n"),
            )

            if summary["reached_extinction"]:
                success_count += 1
                log_event(
                    logger,
                    logging.INFO,
                    (
                        f"Graph {graph_num}/{len(indexed_graphs)} (atlas:{atlas_index}) "
                        f"reached extinction at iteration {summary['extinct_iteration']}"
                    ),
                    event="graph_extinction",
                    run_id=run_id,
                    extra_fields={
                        "graph_num": graph_num,
                        "total_graphs": len(indexed_graphs),
                        "extinct_iteration": summary["extinct_iteration"],
                    },
                )
            else:
                log_event(
                    logger,
                    logging.DEBUG,
                    (
                        f"Graph {graph_num}/{len(indexed_graphs)} (atlas:{atlas_index}) "
                        f"did not reach extinction. Final nodes: {summary['final_nodes']}"
                    ),
                    event="graph_completed",
                    run_id=run_id,
                    extra_fields={
                        "graph_num": graph_num,
                        "total_graphs": len(indexed_graphs),
                        "final_nodes": summary["final_nodes"],
                        "final_edges": summary["final_edges"],
                    },
                )

        log_file.write(
            dumps_record(
                {
                    "event": "scan_end",
                    "scan_id": scan_id,
                    "graphs_count": len(indexed_graphs),
                    "success_count": success_count,
                }
            )
            + "\n"
        )

    log_event(
        logger,
        logging.INFO,
        f"Scan completed. Graphs processed: {len(indexed_graphs)}, "
        f"success count (reached <=1 node): {success_count}",
        event="scan_completed",
        extra_fields={
            "scan_id": scan_id,
            "graphs_count": len(indexed_graphs),
            "success_count": success_count,
            "log_path": str(config.log_path),
        },
    )


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    setup_logging(__name__, verbose=args.verbose)
    run(args.config)


if __name__ == "__main__":
    main()

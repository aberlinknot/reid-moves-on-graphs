"""Run a single weighted random sequence of Reidemeister moves."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.logging_config import log_event, setup_logging

from ..random_move_run_core import dumps_record, load_initial_graph, parse_run_config, run_random_walk

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run weighted random Reidemeister moves.")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to run YAML config.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging.",
    )
    return parser.parse_args()


def run(config_path: Path) -> None:
    """Run weighted random-move loop and write compact JSONL log."""
    config = parse_run_config(config_path)
    graph, source_name = load_initial_graph(config.source)

    config.log_path.parent.mkdir(parents=True, exist_ok=True)
    with config.log_path.open("w", encoding="utf-8") as log_file:
        run_random_walk(
            graph=graph,
            iterations=config.iterations,
            weights=config.weights,
            seed=config.seed,
            run_id=source_name,
            source_name=source_name,
            stop_on_extinction=False,
            on_record=lambda record: log_file.write(dumps_record(record) + "\n"),
        )

    log_event(
        logger,
        logging.INFO,
        f"Run completed. Log written to: {config.log_path}",
        event="run_completed",
        run_id=source_name,
    )


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    setup_logging(__name__, verbose=args.verbose)
    run(args.config)


if __name__ == "__main__":
    main()

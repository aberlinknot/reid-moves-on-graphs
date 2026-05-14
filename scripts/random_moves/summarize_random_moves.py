"""CLI wrapper for log utilities to summarize random-moves JSONL logs."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.logging_config import log_event, setup_logging

from .random_move_log_utils import extract_node_counts, summarize_counts

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute min/max/mean node counts across all log iterations."
    )
    parser.add_argument(
        "--log",
        type=Path,
        required=True,
        help="Path to JSONL log file produced by a random-moves run or atlas scan.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    setup_logging(__name__, verbose=args.verbose)

    try:
        counts_by_run = extract_node_counts(args.log)
        all_counts = [value for counts in counts_by_run.values() for value in counts]

        log_event(
            logger,
            logging.INFO,
            f"Summary statistics from {args.log}:\nOverall:\n{summarize_counts(all_counts)}",
            event="log_summarized",
        )

        print("overall")
        print(summarize_counts(all_counts))

        if len(counts_by_run) > 1:
            for run_id in sorted(counts_by_run):
                print()
                print(f"run_id={run_id}")
                print(summarize_counts(counts_by_run[run_id]))

    except Exception as e:
        log_event(
            logger,
            logging.ERROR,
            f"Error summarizing log: {e}",
            event="summarization_failed",
        )
        raise


if __name__ == "__main__":
    main()

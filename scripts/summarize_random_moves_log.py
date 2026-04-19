"""Summarize node-count statistics from random-moves JSONL logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Compute min/max/mean node counts across all log iterations."
    )
    parser.add_argument(
        "--log",
        type=Path,
        required=True,
        help="Path to JSONL log file produced by run_random_moves.py",
    )
    return parser.parse_args()


def extract_node_counts(log_path: Path) -> list[int]:
    """Extract result_node_count values from iteration records.

    Parameters
    ----------
    log_path : Path
        Path to input JSONL log.

    Returns
    -------
    list[int]
        Node-count values for all iteration records.

    Raises
    ------
    ValueError
        If no valid iteration records are found.
    """
    counts: list[int] = []

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            # Skip non-iteration records, e.g. run_start header.
            if "iteration" not in record:
                continue

            value = record.get("result_node_count")
            if isinstance(value, int):
                counts.append(value)

    if not counts:
        raise ValueError("No iteration records with 'result_node_count' were found.")

    return counts


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    counts = extract_node_counts(args.log)

    min_nodes = min(counts)
    max_nodes = max(counts)
    avg_nodes = sum(counts) / len(counts)

    print(f"iterations={len(counts)}")
    print(f"min_nodes={min_nodes}")
    print(f"max_nodes={max_nodes}")
    print(f"avg_nodes={avg_nodes:.6f}")


if __name__ == "__main__":
    main()

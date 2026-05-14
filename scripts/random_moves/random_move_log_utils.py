"""Utilities for summarizing random-moves JSONL logs."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def extract_node_counts(log_path: Path) -> dict[str, list[int]]:
    """Extract node-count values grouped by run identifier."""
    counts_by_run: dict[str, list[int]] = defaultdict(list)

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            if record.get("event") != "iteration":
                continue

            value = record.get("result_node_count")
            if isinstance(value, int):
                run_id = record.get("run_id")
                if not isinstance(run_id, str) or not run_id:
                    run_id = "__legacy__"
                counts_by_run[run_id].append(value)

    if not counts_by_run:
        raise ValueError("No iteration records with 'result_node_count' were found.")

    return counts_by_run


def summarize_counts(counts: list[int]) -> str:
    """Summarize a sequence of node counts as text lines."""
    min_nodes = min(counts)
    max_nodes = max(counts)
    avg_nodes = sum(counts) / len(counts)

    return "\n".join(
        [
            f"iterations={len(counts)}",
            f"min_nodes={min_nodes}",
            f"max_nodes={max_nodes}",
            f"avg_nodes={avg_nodes:.6f}",
        ]
    )

"""
Draw predefined graphs from YAML files.

All code, comments, and docstrings must be in English (NumPy style).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

from src.parsers.graph_yaml_parser import build_graph, list_graph_configs, parse_graph_yaml
from tools.visualization import draw_graph

Mode = Literal["show", "save", "both"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Draw graphs from YAML presets.")
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("examples/graphs"),
        help="Directory containing one YAML file per graph.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Graph preset name (file stem in examples directory).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Direct path to one YAML graph file. Overrides --name.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available preset names and exit.",
    )
    parser.add_argument(
        "--mode",
        choices=["show", "save", "both"],
        default="show",
        help="Output mode: show, save, or both.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output image path for save/both mode.",
    )
    return parser.parse_args()


def resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve config path from CLI arguments."""
    if args.config is not None:
        return args.config

    if args.name is None:
        raise ValueError("Provide --name or --config, or use --list.")

    return args.examples_dir / f"{args.name}.yaml"


def resolve_output_path(args: argparse.Namespace, config_name: str) -> Path | None:
    """Resolve image output path for save modes."""
    mode: Mode = args.mode
    if mode == "show":
        return None

    if args.output is not None:
        return args.output

    return Path("results/images") / f"{config_name}.png"


def main() -> None:
    """Program entry point for drawing YAML graph presets."""
    args = parse_args()

    if args.list:
        print("Available presets:")
        for file_path in list_graph_configs(args.examples_dir):
            if file_path.stem == "graph_template":
                continue
            print(f"- {file_path.stem}")
        return

    config_path = resolve_config_path(args)
    config = parse_graph_yaml(config_path)
    graph = build_graph(config)

    output_path = resolve_output_path(args, config.name)
    mode: Mode = args.mode
    should_show = mode in {"show", "both"}

    draw_graph(
        graph=graph,
        title=config.title,
        with_labels=config.with_labels,
        output_path=output_path,
        show=should_show,
    )

    if output_path is not None:
        print(f"Saved image: {output_path}")


if __name__ == "__main__":
    main()

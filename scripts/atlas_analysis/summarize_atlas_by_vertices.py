"""Build summary-by-vertices table from atlas analysis CSV.

The script reads ``results/tables/atlas_analysis.csv`` and writes
``results/tables/atlas_summary_by_vertices.csv``.

Aggregates per-graph metrics by vertex count (0–7 vertices). For each vertex
class, computes:

- Number of graphs in that class
- Number of connected graphs
- Number of stuck graphs (no move I or II)
- Number of distinct III-classes
- Number of stuck III-classes (all members stuck)
- Number of graphs in stuck III-classes

Examples
--------
Via module::

    python -m scripts.atlas_analysis.summarize_atlas_by_vertices

With custom paths::

    python -m scripts.atlas_analysis.summarize_atlas_by_vertices \
        --analysis-input /tmp/atlas.csv \
        --summary-output /tmp/atlas_summary.csv

Output CSV contains columns:
    num_vertices, num_graphs, num_connected_graphs, num_stuck_graphs,
    num_iii_classes, num_stuck_iii_classes, num_graphs_in_stuck_iii_classes
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _to_bool_series(series: pd.Series) -> pd.Series:
    """Convert a mixed boolean-like series to booleans.

    Parameters
    ----------
    series : pd.Series
        Input values.

    Returns
    -------
    pd.Series
        Boolean series.
    """
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({'1', 'true', 't', 'yes'})


def build_summary(analysis_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate summary metrics by number of vertices.

    Parameters
    ----------
    analysis_df : pd.DataFrame
        Detailed analysis table.

    Returns
    -------
    pd.DataFrame
        Summary table grouped by ``num_vertices``.
    """
    required_columns = {
        'graph_index',
        'num_vertices',
        'is_connected',
        'is_stuck_graph',
        'iii_class_id',
        'is_in_stuck_class',
    }
    missing = required_columns - set(analysis_df.columns)
    if missing:
        raise ValueError(f'Missing required columns in analysis table: {sorted(missing)}')

    working = analysis_df.copy()
    working['is_connected'] = _to_bool_series(working['is_connected'])
    working['is_stuck_graph'] = _to_bool_series(working['is_stuck_graph'])
    working['is_in_stuck_class'] = _to_bool_series(working['is_in_stuck_class'])

    grouped_rows: list[dict[str, int]] = []
    for num_vertices, group in working.groupby('num_vertices', sort=True):
        grouped_rows.append(
            {
                'num_vertices': int(num_vertices),
                'num_graphs': int(len(group)),
                'num_connected_graphs': int(group['is_connected'].sum()),
                'num_stuck_graphs': int(group['is_stuck_graph'].sum()),
                'num_iii_classes': int(group['iii_class_id'].nunique()),
                'num_stuck_iii_classes': int(
                    group.loc[group['is_in_stuck_class'], 'iii_class_id'].nunique()
                ),
                'num_graphs_in_stuck_iii_classes': int(group['is_in_stuck_class'].sum()),
            }
        )

    return pd.DataFrame(grouped_rows).sort_values('num_vertices').reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed argument object.
    """
    parser = argparse.ArgumentParser(
        description='Build per-vertex summary from atlas_analysis.csv.'
    )
    parser.add_argument(
        '--analysis-input',
        type=Path,
        default=Path('results/tables/atlas_analysis.csv'),
        help='Path to input atlas analysis CSV.',
    )
    parser.add_argument(
        '--summary-output',
        type=Path,
        default=Path('results/tables/atlas_summary_by_vertices.csv'),
        help='Path to output summary CSV.',
    )
    return parser.parse_args()


def main() -> None:
    """Run summary generation.

    Reads atlas_analysis.csv, aggregates metrics by num_vertices, and exports
    to summary CSV with per-vertex-class statistics.

    Example
    -------
    Run with default paths::

        python -m scripts.atlas_analysis.summarize_atlas_by_vertices

    Run with custom analysis input and output::

        python -m scripts.atlas_analysis.summarize_atlas_by_vertices \
            --analysis-input /tmp/atlas_data.csv \
            --summary-output /tmp/summary_by_v.csv
    """
    args = parse_args()
    analysis_df = pd.read_csv(args.analysis_input)
    summary_df = build_summary(analysis_df)

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(args.summary_output, index=False)

    print(f'Summary table written: {args.summary_output} ({len(summary_df)} rows)')


"""CLI entry points for project scripts.

This package contains executable scripts for graph analysis, visualization,
and Reidemeister move research:

- ``atlas_analysis``: Compute statistics on the NetworkX graph atlas and
  summarize metrics by vertex count.
- ``parity_bracket``: Analyze parity bracket invariants.
- ``random_moves``: Run random Reidemeister move sequences.

All scripts can be run as modules::

  python -m scripts.atlas_analysis.analyze_atlas
  python -m scripts.atlas_analysis.summarize_atlas_by_vertices
  python -m scripts.random_moves.single_run.random_move_single_run
  python -m scripts.random_moves.atlas_run.random_move_atlas_run
"""

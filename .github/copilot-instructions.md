# Copilot Instructions for reid-moves-on-graphs

This is a research project on Reidemeister moves on graphs (inherited from knot theory).

## Language
- All source code, inline comments, and docstrings must be written in **English**.
- All user-facing documentation (README, usage guides, markdown docs) must be written in **Russian**.
- This file and copilot-instructions are in English.

## Docstring style
- Use **NumPy-style** docstrings for all functions, classes, and modules.

## Commit and branch naming
- All commit messages and branch names must be in **English**.
- Follow **Conventional Commits** format: `type(scope): description`.
  - Common types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `style`.
  - Bullet points in the body start with a **capital letter**.
  - No `BREAKING CHANGE` footer unless an existing public API is changed.

## Dependencies
- All runtime and dev dependencies must be pinned with exact versions (`==version`) in `requirements.txt` and `requirements-dev.txt`.

## Typing
- Use Python `typing` module and standard annotations throughout.
- Avoid `Any` in core logic; use it only at system boundaries.
- Prefer `Node = Hashable`, `Edge = tuple[Node, Node]` type aliases for graph types.
- Docstrings for types should reflect the alias names, not raw types.

## Code style
- Line length: **100 characters** (enforced by black, isort, flake8).
- Formatter: **black** (prefer single quotes except docstrings, set `skip-string-normalization = true`).
- Import order: **isort** with black profile.
- Linter: **flake8** (ignore E203, W503).

## Project structure
- `src/` — core source modules (graph objects, parsers, moves).
- `tools/` — executable CLI scripts and visualization utilities.
- `examples/graphs/` — one YAML file per graph preset.
- `results/images/` — generated output images (gitignored except `.gitkeep`).
- `tests/` — tests (minimal coverage, growing with the project).
- `docs/` — markdown documentation files.
- `scripts/` — research and experimental scripts.

## YAML graph config format
- One file per graph in `examples/graphs/`.
- Use `graph_template.yaml` as a reference for new configs.
- All YAML reading must go through `src/parsers/graph_yaml_parser.py`.

## Visualization
- Use `tools/visualization.py` for all graph drawing.
- Support `show`, `save`, `both` modes via CLI flags.
- Default save path: `results/images/<name>.png`.

---

> Human-readable version of these rules (in Russian): [`RULES.md`](../RULES.md). Keep both files in sync when updating conventions.

# Случайные движения на графах (Random Walks)

## Одиночный прогон

Пример запуска случайных движений на треугольнике (50 итераций):

```bash
python -m scripts.random_moves.single_run.random_move_single_run \
  --config scripts/random_moves/single_run/configs/random_moves_triangle.yaml
```

## Пакетный скан atlas (все графы)

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml
```

## Пакетный скан 6-вершинных графов

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan_6_vertices.yaml
```

## Прогресс выполнения

Для просмотра прогресса используйте флаг `--verbose` (или `-v`):

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml \
  --verbose
```

## Анализ логов

Подсчёт минимума, максимума и среднего числа вершин:

```bash
python -m scripts.random_moves.summarize_random_moves \
  --log scripts/random_moves/single_run/logs/random_moves_triangle.jsonl
```

## Где искать логи
- `scripts/random_moves/single_run/logs/` — для одиночных прогонов
- `scripts/random_moves/atlas_run/logs/` — для пакетных сканов

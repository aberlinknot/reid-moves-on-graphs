# Формат YAML-конфигов

## Пример конфига для одиночного прогона

```yaml
iterations: 50
seed: 7
log_path: scripts/random_moves/single_run/logs/random_moves_triangle.jsonl

source:
  type: yaml
  yaml_path: examples/graphs/triangle.yaml

weights:
  move_1_add: 0.10
  move_1_remove: 0.10
  move_2_add: 0.20
  move_2_remove: 0.20
  move_3: 0.40
```

## Пример конфига для atlas scan

```yaml
iterations: 1000
seed: 10
log_path: scripts/random_moves/atlas_run/logs/random_moves_atlas_scan.jsonl

scan:
  node_count: null
  limit: null

weights:
  move_1_add: 0.05
  move_1_remove: 0.10
  move_2_add: 0.15
  move_2_remove: 0.20
  move_3: 0.50
```

## Описание ключей
- `iterations` — число итераций
- `seed` — базовое значение для генератора случайных чисел
- `log_path` — путь для сохранения лога
- `source` — описание исходного графа (yaml/manual/atlas)
- `weights` — веса для каждого типа движения
- `scan.node_count` — фильтр по числу вершин (atlas scan)
- `scan.limit` — ограничение числа графов (atlas scan)

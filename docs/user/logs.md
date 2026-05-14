# Логи и анализ результатов

## Где искать логи
- `scripts/random_moves/single_run/logs/` — одиночные прогоны
- `scripts/random_moves/atlas_run/logs/` — пакетные сканы

## Формат логов
- JSONL (одна строка — одно событие)
- Ключевые поля: `event`, `run_id`, `iteration`, `result_node_count`, ...

## Пример анализа логов

```bash
python -m scripts.random_moves.summarize_random_moves \
  --log scripts/random_moves/single_run/logs/random_moves_triangle.jsonl
```

## Фильтрация событий

```bash
# Все завершения запусков по графам
cat scripts/random_moves/atlas_run/logs/random_moves_atlas_scan.jsonl | grep '"event": "run_end"'

# С помощью jq
cat scripts/random_moves/atlas_run/logs/random_moves_atlas_scan.jsonl | jq 'select(.event == "run_end" and .reached_extinction == true)'
```

## Пример вывода
```
iterations=50
min_nodes=2
max_nodes=20
avg_nodes=12.680000
```

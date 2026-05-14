# Atlas анализ графов

Скрипты для анализа полного атласа графов NetworkX и подсчёта статистики по ходам Рейдемейстера.

## Общее описание

Атлас NetworkX содержит 1253 граф с числом вершин от 0 до 7. Данный инструмент анализирует каждый граф в атласе и вычисляет:

1. **Кандидаты и результаты ходов** — для каждого типа хода Рейдемейстера (I, II, III) выявляются возможные кандидаты и соответствующие им графы-результаты
2. **Связность** — связен ли граф
3. **Застреванием** — является ли граф "застрявшим" (нет ходов I и II)
4. **III-класс** — принадлежность к классам эквивалентности под действием хода III

## Скрипты

### `analyze_atlas.py` — детальный анализ

Вычисляет полный анализ каждого графа атласа и экспортирует результаты в CSV.

**Запуск:**

```bash
python -m scripts.atlas_analysis.analyze_atlas
```

**Параметры:**

- `--analysis-output PATH` — путь для сохранения результатов (по умолчанию: `results/tables/atlas_analysis.csv`)

**Пример:**

```bash
python -m scripts.atlas_analysis.analyze_atlas --analysis-output /tmp/atlas.csv
```

**Результат:** CSV таблица с колонками:
- `graph_index` — порядковый номер графа в атласе
- `num_vertices` — количество вершин
- `num_edges` — количество рёбер
- `edges` — список рёбер (в формате `(u, v); (u, v); ...`)
- `move_1_candidates`, `move_1_results` — кандидаты и результаты хода I
- `move_2_candidates`, `move_2_results` — кандидаты и результаты хода II
- `move_3_candidates`, `move_3_results` — кандидаты и результаты хода III
- `is_connected` — связен ли граф
- `is_stuck_graph` — нет ли ходов I и II
- `iii_class_id` — ID III-класса эквивалентности
- `size_of_iii_class` — размер III-класса
- `is_in_stuck_class` — все ли графы в III-классе застряли

### `summarize_atlas_by_vertices.py` — агрегация по числу вершин

Считывает результаты анализа и агрегирует метрики по числу вершин.

**Запуск:**

```bash
python -m scripts.atlas_analysis.summarize_atlas_by_vertices
```

**Параметры:**

- `--analysis-input PATH` — путь к входной CSV таблице (по умолчанию: `results/tables/atlas_analysis.csv`)
- `--summary-output PATH` — путь для сохранения результатов (по умолчанию: `results/tables/atlas_summary_by_vertices.csv`)

**Пример:**

```bash
python -m scripts.atlas_analysis.summarize_atlas_by_vertices \
    --analysis-input /tmp/atlas.csv \
    --summary-output /tmp/summary.csv
```

**Результат:** CSV таблица с колонками (по одной строке на каждое число вершин 0–7):
- `num_vertices` — количество вершин
- `num_graphs` — число графов с этим количеством вершин
- `num_connected_graphs` — из них связных
- `num_stuck_graphs` — из них застрявших
- `num_iii_classes` — число различных III-классов
- `num_stuck_iii_classes` — число III-классов, где все графы застряли
- `num_graphs_in_stuck_iii_classes` — число графов, принадлежащих застрявшим III-классам

## Полный рабочий процесс

```bash
# 1. Вычислить анализ для всех графов атласа
python -m scripts.atlas_analysis.analyze_atlas

# 2. Агрегировать результаты по числу вершин
python -m scripts.atlas_analysis.summarize_atlas_by_vertices

# 3. Результаты сохранены в:
# - results/tables/atlas_analysis.csv (1253 строки)
# - results/tables/atlas_summary_by_vertices.csv (8 строк)
```

## Примеры использования в Python

```python
import pandas as pd

# Загрузить детальные результаты
analysis = pd.read_csv('results/tables/atlas_analysis.csv')
print(analysis.head())

# Загрузить агрегированные результаты
summary = pd.read_csv('results/tables/atlas_summary_by_vertices.csv')
print(summary)

# Посмотреть на застрявшие графы
stuck_graphs = analysis[analysis['is_stuck_graph']]
print(f"Застрявших графов: {len(stuck_graphs)}")

# Посмотреть на распределение по III-классам
print(analysis.groupby('iii_class_id').size().describe())
```

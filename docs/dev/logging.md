# Логирование в проекте

Проект использует встроенный модуль Python `logging` с кастомным JSON форматированием для структурированного логирования.

## Архитектура

### Компоненты

- **`src/logging_config.py`** — центральный модуль конфигурации
  - `JSONFormatter` — форматирует логи в JSON для файлов (JSONL формат)
  - `ConsoleFormatter` — красивое форматирование для консоли с цветами
  - `setup_logging(name, log_file=None)` — инициализирует логгер с консолью; файл подключается только при переданном `log_file`
  - `log_event(logger, level, message, event, run_id, extra_fields)` — логирует структурированное событие

### Вывод

**Консоль** (красивый, читаемый):
```
[18:23:43] [INFO    ] __main__ | event=list_presets
  Listing available graph presets
```

**Файл** (JSONL, структурированный):
```json
{"timestamp": "2026-05-14 18:23:43", "level": "INFO", "logger": "scripts.random_moves.single_run.random_move_single_run", "message": "Run completed. Log written to: ...", "event": "run_completed", "run_id": "yaml:examples/graphs/triangle.yaml"}
```

## Использование

### В скрипте (CLI точка входа)

```python
import logging
from pathlib import Path
from src.logging_config import setup_logging, log_event

logger = logging.getLogger(__name__)

def main():
    setup_logging(__name__, log_file=Path("logs/process.jsonl"))  # Инициализировать на входе

    log_event(
        logger,
        logging.INFO,
        "Process started",
        event="process_started",
        run_id="my_run_123",
    )
```

### В модуле (без главной функции)

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Something happened")  # Обычное логирование

    # Или структурированное
  log_event(
    logger,
    logging.INFO,
    "Event happened",
    event="my_event",
    run_id="run_123",
  )
```

## Уровни логирования

- `DEBUG` — детальная информация для диагностики
- `INFO` — информационные сообщения (ход выполнения)
- `WARNING` — предупреждения (что-то неожиданное, но не ошибка)
- `ERROR` — ошибки (что-то пошло не так)
- `CRITICAL` — критические ошибки (приложение может упасть)

## Поля в JSON логе

### Базовые (всегда присутствуют)
- `timestamp` — время в формате `YYYY-MM-DD HH:MM:SS`
- `level` — уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger` — имя логгера (обычно модуль)
- `message` — основное сообщение

### Дополнительные (если заданы)
- `event` — тип события (например, "run_completed", "scan_started")
- `run_id` — идентификатор запуска для корреляции
- `exception` — информация об исключении (если есть)
- `extra_fields` — объект с пользовательскими полями

## Пример: Random Moves

В `scripts/random_moves/single_run/random_move_single_run.py`:

```python
def main():
    setup_logging(__name__, verbose=args.verbose)  # Инициализировать

    log_event(
        logger,
        logging.INFO,
        f"Run completed. Log written to: {config.log_path}",
        event="run_completed",
        run_id=source_name,
    )
```

  Примечание: JSONL с результатами random walks пишется отдельно через `config.log_path`
  в коде runner-а, а не через `setup_logging(log_file=...)`.

Вывод в консоль:
```
[18:23:23] [INFO    ] __main__ | event=run_completed | run_id=yaml:examples/graphs/triangle.yaml
  Run completed. Log written to: scripts\random_moves\single_run\logs\random_moves_triangle.jsonl
```

Вывод в файл (JSONL):
```json
{"timestamp": "2026-05-14 18:23:23", "level": "INFO", "logger": "scripts.random_moves.single_run.random_move_single_run", "message": "Run completed. Log written to: ...", "event": "run_completed", "run_id": "yaml:examples/graphs/triangle.yaml"}
```

## Миграция от print()

### До
```python
print(f"Process started with {count} items")
print("Error occurred!")
```

### После
```python
logger = logging.getLogger(__name__)

logger.info(f"Process started with {count} items")
logger.error("Error occurred!")

# Или со структурированными полями
log_event(logger, logging.INFO, f"Process started with {count} items", event="process_start", extra_fields={"count": count})
```

## Анализ логов

### Парсинг JSONL логов

```python
import json
from pathlib import Path

with open("log.jsonl") as f:
    for line in f:
        record = json.loads(line)
        print(f"[{record['level']}] {record['message']}")
```

### Фильтрация по событию

```bash
# Найти все события типа "run_completed"
grep '"event": "run_completed"' log.jsonl

# Или с jq
cat log.jsonl | jq 'select(.event == "run_completed")'
```

### Фильтрация по run_id

```bash
# Найти все логи для конкретного запуска
grep '"run_id": "run_123"' log.jsonl

# С jq
cat log.jsonl | jq "select(.run_id == \"run_123\")"
```

## Просмотр прогресса

### Режим INFO (по умолчанию)

Показывает основные события (начало/конец операции, критические результаты):

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml
```

Вывод:
```
[18:30:17] [INFO    ] __main__ | event=scan_start
  Starting atlas scan: random_moves_atlas_scan. Graphs to process: 1253
[18:30:17] [INFO    ] __main__ | event=graph_extinction | run_id=atlas:0
  Graph 1/1253 (atlas:0) reached extinction at iteration 5
[18:30:17] [INFO    ] __main__ | event=graph_extinction | run_id=atlas:1
  Graph 2/1253 (atlas:1) reached extinction at iteration 12
...
[18:30:45] [INFO    ] __main__ | event=scan_completed
  Scan completed. Graphs processed: 1253, success count (reached <=1 node): 1195
```

### Режим DEBUG (с флагом -v/--verbose)

Показывает полный прогресс включая начало обработки каждого графа:

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml \
  --verbose
```

Вывод:
```
[18:30:17] [INFO    ] __main__ | event=scan_start
  Starting atlas scan: random_moves_atlas_scan. Graphs to process: 1253
[18:30:17] [DEBUG   ] __main__ | event=graph_start | run_id=atlas:0
  Processing graph 1/1253: atlas_index=0, nodes=0, edges=0
[18:30:17] [INFO    ] __main__ | event=graph_extinction | run_id=atlas:0
  Graph 1/1253 (atlas:0) reached extinction at iteration 5
[18:30:17] [DEBUG   ] __main__ | event=graph_start | run_id=atlas:1
  Processing graph 2/1253: atlas_index=1, nodes=1, edges=0
[18:30:17] [INFO    ] __main__ | event=graph_extinction | run_id=atlas:1
  Graph 2/1253 (atlas:1) reached extinction at iteration 12
...
```

### Доступные флаги

Все CLI скрипты поддерживают флаг `-v / --verbose`:
- `python -m scripts.random_moves.single_run.random_move_single_run --config ... --verbose`
- `python -m scripts.random_moves.atlas_run.random_move_atlas_run --config ... --verbose`
- `python -m scripts.random_moves.summarize_random_moves --log ... --verbose`
- `python -m tools.draw_examples --name ... --verbose`

---

Система позволяет одновременно иметь:
- 🎨 Красивый вывод для разработчика в консоль
- 📊 Структурированные логи для анализа и дебага в JSON
- 🔍 Возможность фильтрации по событиям, запускам и контексту
- 📈 Отслеживание прогресса длительных операций

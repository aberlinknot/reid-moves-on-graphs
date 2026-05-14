# Reidemeister Moves on Graphs

Исследовательский проект по изучению эквивалентности графов относительно движений Рейдемейстера (наследованных из теории узлов).

> Проект разрабатывается и тестируется на Python 3.12.10 (другие версии не гарантируются).

## Цели
- Формализация и программная реализация движений Рейдемейстера на графах
- Автоматизация поиска классов эквивалентности
- Проверка гипотез и проведение вычислительных экспериментов

- `articles/` — черновики, препринты, статьи (tex/pdf) и вспомогательная литература
- `src/` — основной код (модули для работы с графами и движениями)
- `tests/` — тесты
- `docs/` — документация
- `examples/` — набор YAML-конфигов графов (по одному файлу на граф)
- `results/` — результаты запусков (например, сохранённые изображения)
- `scripts/` — исследовательские и демонстрационные скрипты, конфиги и логи экспериментов
- `tools/` — утилиты (например, визуализация и запуск примеров)
- `requirements.txt` — основные зависимости
- `requirements-dev.txt` — dev-зависимости для разработки


## Установка и настройка

Минимальный пример (Python 3.12.10):

```bash
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate для Windows
pip install -r requirements.txt
```

Подробная инструкция: [docs/user/install.md](docs/user/install.md)

## Визуализация графов

Пример:
```bash
python -m tools.draw_examples --name triangle
```
Подробно: [docs/user/visualization.md](docs/user/visualization.md)

## Случайные движения (random walks)

Пример одиночного прогона:
```bash
python -m scripts.random_moves.single_run.random_move_single_run \
	--config scripts/random_moves/single_run/configs/random_moves_triangle.yaml
```
Пример пакетного сканирования:
```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
	--config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml
```
Подробно: [docs/user/random_walks.md](docs/user/random_walks.md)
## Документация

- [Пользовательские инструкции (user)](docs/user/README.md)
- [Математическая часть (math)](docs/math/)
- [Техническая часть (dev)](docs/dev/)

Вывод показывает статистику по всем итерациям, а при наличии нескольких run_id в логе — отдельно по каждому.

## Логирование

Проект использует структурированное логирование через встроенный модуль `logging` с кастомным JSON форматированием.

**Консоль** — красивый вывод с цветами:
```
[18:23:43] [INFO    ] module_name | event=process_started | run_id=run_123
  Process started successfully
```

**Файлы** — JSONL формат (строка = одна запись JSON) для анализа и фильтрации:
```json
{"timestamp": "2026-05-14 18:23:43", "level": "INFO", "logger": "scripts.module", "message": "Process started", "event": "process_started", "run_id": "run_123"}
```

Подробнее: [docs/logging.md](docs/logging.md)

## Документация
Документация будет пополняться по мере развития проекта. Основные сведения — в Markdown-файлах в `docs/` и docstring'ах в коде.

Правила оформления и соглашения: см. [RULES.md](RULES.md)

---
Проект находится в активной разработке.
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


## Установка и настройка окружения

1. Создайте виртуальное окружение (один из вариантов):
	 - Windows (cmd):
		 ```cmd
		 python -m venv .venv
		 .venv\Scripts\activate
		 ```
	 - Windows (PowerShell):
		 ```powershell
		 python -m venv .venv
		 .venv\Scripts\Activate.ps1
		 ```
	 - Windows (Git Bash):
		 ```bash
		 python -m venv .venv
		 source .venv/Scripts/activate
		 ```
	 - Linux/macOS:
		 ```bash
		 python -m venv .venv
		 source .venv/bin/activate
		 ```

2. Установите основные зависимости:
	 ```bash
	 pip install -r requirements.txt
	 ```

3. (Рекомендуется) Установите dev-зависимости:
	 ```bash
	 pip install -r requirements-dev.txt
	 ```

4. Ознакомьтесь с `RULES.md` и заметками в `docs/`
5. Запустите примеры из scripts/ или создайте свой скрипт

## Быстрая визуализация из YAML
Для редактируемого набора базовых графов используйте директорию `examples/graphs/` и скрипт:

```bash
python -m tools.draw_examples --name triangle
```

Чтобы посмотреть список доступных графов:

```bash
python -m tools.draw_examples --list
```

Сохранить рисунок в `results/images/` без открытия окна:

```bash
python -m tools.draw_examples --name triangle --mode save
python -m tools.draw_examples --name square_with_diagonal --mode save
```

Сохранить и показать одновременно:

```bash
python -m tools.draw_examples --name triangle --mode both
```

## Случайные движения с весами

**Одиночный прогон** с треугольником (50 итераций):

```bash
python -m scripts.random_moves.single_run.random_move_single_run \
  --config scripts/random_moves/single_run/configs/random_moves_triangle.yaml
```

Шаблон полного конфига с примерами источников `yaml`, `manual`, `atlas`:

```text
scripts/random_moves/single_run/configs/random_moves_template.yaml
```

**Пакетный скан atlas** (все графы):

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml
```

**Пакетный скан 6-вершинных графов** (reduction-only с нулевыми весами add-ходов):

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan_6_vertices.yaml
```

Логи сохраняются в JSONL-формате в:
- `scripts/random_moves/single_run/logs/` — для одиночных прогонов
- `scripts/random_moves/atlas_run/logs/` — для пакетных сканов

Для просмотра **прогресса** длительных операций используйте флаг `--verbose` (или `-v`):

```bash
python -m scripts.random_moves.atlas_run.random_move_atlas_run \
  --config scripts/random_moves/atlas_run/configs/random_moves_atlas_scan.yaml \
  --verbose
```

Вывод прогресса (INFO уровень по умолчанию):
```
[HH:MM:SS] [INFO    ] __main__ | event=graph_extinction | run_id=atlas:0
  Graph 1/1202 (atlas:0) reached extinction at iteration 5
```

С `--verbose` добавляется полная информация о каждом графе (DEBUG уровень).

**Анализ логов** — подсчёт минимума, максимума и среднего числа вершин:

```bash
python -m scripts.random_moves.summarize_random_moves \
  --log scripts/random_moves/single_run/logs/random_moves_triangle.jsonl
```

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
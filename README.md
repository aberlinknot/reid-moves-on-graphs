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
- `scripts/` — исследовательские и демонстрационные скрипты
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
Для длинного цикла случайных движений используйте:

```bash
python -m scripts.run_random_moves --config examples/run_configs/random_moves_triangle.yaml
```

Шаблон полного конфига с источниками `yaml/manual/atlas`:

```text
examples/run_configs/random_moves_template.yaml
```


## Документация
Документация будет пополняться по мере развития проекта. Основные сведения — в Markdown-файлах в `docs/` и docstring'ах в коде.

Правила оформления и соглашения: см. [RULES.md](RULES.md)

---
Проект находится в активной разработке.
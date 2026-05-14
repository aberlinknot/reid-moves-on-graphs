# Визуализация графов

Для быстрой визуализации используйте скрипт `tools/draw_examples.py`.

## Просмотр доступных графов

```bash
python -m tools.draw_examples --list
```

## Визуализация одного графа

```bash
python -m tools.draw_examples --name triangle
```

## Сохранение изображения

```bash
python -m tools.draw_examples --name triangle --mode save
```

## Сохранение и показ одновременно

```bash
python -m tools.draw_examples --name triangle --mode both
```

## Дополнительные параметры
- `--examples-dir` — путь к директории с YAML-графами (по умолчанию examples/graphs/)
- `--output` — путь для сохранения изображения
- `-v/--verbose` — подробный лог (DEBUG)

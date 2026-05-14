# Установка и настройка

1. Создайте виртуальное окружение (Python 3.12.10):
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
   - Linux/macOS:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # (опционально)
   ```

3. Ознакомьтесь с `RULES.md` и документацией в папке docs/

4. Проверьте запуск примеров (см. отдельные инструкции по CLI)

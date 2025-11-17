#!/bin/bash
# Скрипт запуска бота

# Переход в директорию скрипта
cd "$(dirname "$0")"

# Активация виртуального окружения (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск бота
echo "Запуск бота..."
python3 bot.py

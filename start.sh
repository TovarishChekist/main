#!/bin/bash

# Скрипт для быстрого запуска бота

echo "🔐 Telegram Encryption Bot - Startup Script"
echo "==========================================="

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте .env файл из .env.example:"
    echo "cp .env.example .env"
    echo "И добавьте ваш TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Проверка наличия токена
if ! grep -q "TELEGRAM_BOT_TOKEN=.*[^=]" .env; then
    echo "⚠️  TELEGRAM_BOT_TOKEN не установлен в .env файле!"
    echo "Получите токен от @BotFather и добавьте в .env"
    exit 1
fi

# Создание виртуального окружения если не существует
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Установка/обновление зависимостей
echo "📥 Установка зависимостей..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Создание необходимых директорий
mkdir -p data logs

# Запуск бота
echo "🚀 Запуск бота..."
echo "==========================================="
python bot.py

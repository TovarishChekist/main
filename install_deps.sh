#!/bin/bash
# Скрипт установки зависимостей для Telegram бота

echo "========================================="
echo "Установка зависимостей для Telegram бота"
echo "========================================="
echo ""

# Проверка виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Виртуальное окружение не активировано!"
    echo ""
    echo "Пожалуйста, выполните сначала:"
    echo "  cd ~/telegram-bot"
    echo "  source venv/bin/activate"
    echo ""
    exit 1
fi

echo "✓ Виртуальное окружение активировано: $VIRTUAL_ENV"
echo ""

# Показываем текущую версию aiogram
echo "Текущая версия aiogram:"
pip show aiogram 2>/dev/null | grep Version || echo "  (не установлен)"
echo ""

# Удаляем старую версию aiogram
echo "Удаление старой версии aiogram..."
pip uninstall aiogram -y 2>/dev/null
echo ""

# Устанавливаем правильные версии
echo "Установка зависимостей из requirements.txt..."
pip install -r requirements.txt
echo ""

# Проверяем установку
echo "========================================="
echo "Проверка установленных пакетов:"
echo "========================================="
pip show aiogram | grep -E "Name:|Version:"
pip show python-dotenv | grep -E "Name:|Version:"
pip show aiosqlite | grep -E "Name:|Version:"
echo ""

# Проверяем версию aiogram
AIOGRAM_VERSION=$(pip show aiogram | grep Version | cut -d' ' -f2)
if [[ "$AIOGRAM_VERSION" == 3.3.0 ]]; then
    echo "✅ Все зависимости установлены правильно!"
    echo ""
    echo "Теперь можете запустить бота:"
    echo "  python main.py"
else
    echo "⚠️  Версия aiogram не соответствует требуемой (нужна 3.3.0, установлена $AIOGRAM_VERSION)"
    echo ""
    echo "Попробуйте установить вручную:"
    echo "  pip install aiogram==3.3.0"
fi
echo ""

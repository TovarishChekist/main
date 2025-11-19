#!/bin/bash
# Помощник для развертывания на PythonAnywhere

echo "=========================================="
echo "  Telegram Appeals Bot - Deploy Helper"
echo "=========================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Функция для вывода предупреждения
warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Функция для вывода ошибки
error() {
    echo -e "${RED}✗${NC} $1"
}

# Проверка наличия Python
echo "Проверка окружения..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python установлен: $PYTHON_VERSION"
else
    error "Python не найден! Установите Python 3.8 или выше"
    exit 1
fi

# Проверка наличия git
if command -v git &> /dev/null; then
    success "Git установлен"
else
    warning "Git не найден (опционально для обновлений)"
fi

echo ""
echo "Выберите действие:"
echo "1) Первичная установка (новое развертывание)"
echo "2) Обновление бота (git pull + установка зависимостей)"
echo "3) Проверка конфигурации"
echo "4) Тестовый запуск"
echo "5) Выход"
echo ""
read -p "Введите номер действия: " choice

case $choice in
    1)
        echo ""
        echo "=== ПЕРВИЧНАЯ УСТАНОВКА ==="

        # Создание виртуального окружения
        if [ ! -d "venv" ]; then
            echo "Создание виртуального окружения..."
            python3 -m venv venv
            success "Виртуальное окружение создано"
        else
            warning "Виртуальное окружение уже существует"
        fi

        # Активация и установка зависимостей
        echo "Установка зависимостей..."
        source venv/bin/activate
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r requirements.txt
        success "Зависимости установлены"

        # Создание .env файла
        if [ ! -f ".env" ]; then
            echo ""
            echo "Настройка переменных окружения..."
            cp .env.example .env
            success "Файл .env создан из шаблона"
            warning "ВАЖНО: Отредактируйте файл .env и укажите:"
            echo "  - BOT_TOKEN (получите от @BotFather)"
            echo "  - ADMIN_ID (получите от @userinfobot)"
            echo ""
            read -p "Нажмите Enter для редактирования .env или Ctrl+C для выхода..."

            if command -v nano &> /dev/null; then
                nano .env
            elif command -v vim &> /dev/null; then
                vim .env
            else
                warning "Редактор не найден. Отредактируйте .env вручную"
            fi
        else
            warning "Файл .env уже существует"
        fi

        success "Установка завершена!"
        echo ""
        echo "Следующие шаги:"
        echo "1. Убедитесь, что .env настроен правильно"
        echo "2. Запустите тестовый запуск (опция 4)"
        echo "3. Настройте Always-On Task в PythonAnywhere"
        ;;

    2)
        echo ""
        echo "=== ОБНОВЛЕНИЕ БОТА ==="

        # Git pull
        if [ -d ".git" ]; then
            echo "Получение обновлений из Git..."
            git pull
            success "Код обновлен"
        else
            warning "Это не Git репозиторий, пропускаем git pull"
        fi

        # Обновление зависимостей
        echo "Обновление зависимостей..."
        source venv/bin/activate
        pip install -r requirements.txt --upgrade
        success "Зависимости обновлены"

        success "Обновление завершено!"
        warning "Не забудьте перезапустить Always-On Task в PythonAnywhere"
        ;;

    3)
        echo ""
        echo "=== ПРОВЕРКА КОНФИГУРАЦИИ ==="

        # Проверка .env
        if [ -f ".env" ]; then
            success "Файл .env существует"

            # Проверка BOT_TOKEN
            if grep -q "BOT_TOKEN=your_bot_token_here" .env; then
                error "BOT_TOKEN не настроен! Отредактируйте .env"
            elif grep -q "BOT_TOKEN=" .env; then
                success "BOT_TOKEN настроен"
            else
                error "BOT_TOKEN отсутствует в .env"
            fi

            # Проверка ADMIN_ID
            if grep -q "ADMIN_ID=your_telegram_id_here" .env; then
                error "ADMIN_ID не настроен! Отредактируйте .env"
            elif grep -q "ADMIN_ID=" .env; then
                success "ADMIN_ID настроен"
            else
                error "ADMIN_ID отсутствует в .env"
            fi
        else
            error "Файл .env не найден!"
        fi

        # Проверка виртуального окружения
        if [ -d "venv" ]; then
            success "Виртуальное окружение существует"
        else
            error "Виртуальное окружение не найдено!"
        fi

        # Проверка зависимостей
        if [ -d "venv" ]; then
            source venv/bin/activate
            echo ""
            echo "Установленные пакеты:"
            pip list | grep -E "(aiogram|aiosqlite|python-dotenv)"
        fi
        ;;

    4)
        echo ""
        echo "=== ТЕСТОВЫЙ ЗАПУСК ==="

        if [ ! -f ".env" ]; then
            error "Файл .env не найден! Выполните сначала установку (опция 1)"
            exit 1
        fi

        if [ ! -d "venv" ]; then
            error "Виртуальное окружение не найдено! Выполните сначала установку (опция 1)"
            exit 1
        fi

        warning "Бот будет запущен в тестовом режиме"
        warning "Для остановки нажмите Ctrl+C"
        echo ""
        read -p "Нажмите Enter для запуска..."

        source venv/bin/activate
        python bot.py
        ;;

    5)
        echo "Выход..."
        exit 0
        ;;

    *)
        error "Неверный выбор!"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Для получения помощи см. PYTHONANYWHERE_DEPLOY.md"
echo "=========================================="

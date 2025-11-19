#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Заголовок
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   Telegram Encryption Bot - PythonAnywhere Setup    ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка, что скрипт запущен на PythonAnywhere
if [[ ! $(hostname) =~ pythonanywhere.com ]]; then
    print_warning "Этот скрипт предназначен для PythonAnywhere"
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Получаем текущую директорию
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

print_info "Директория проекта: $PROJECT_DIR"

# Шаг 1: Создание виртуального окружения
print_info "Шаг 1/7: Создание виртуального окружения..."

if [ -d "$PROJECT_DIR/venv" ]; then
    print_warning "Виртуальное окружение уже существует"
    read -p "Пересоздать? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR/venv"
    fi
fi

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3.10 -m venv "$PROJECT_DIR/venv" || print_error "Не удалось создать venv"
    print_success "Виртуальное окружение создано"
else
    print_success "Используем существующее venv"
fi

# Активация venv
source "$PROJECT_DIR/venv/bin/activate" || print_error "Не удалось активировать venv"
print_success "Виртуальное окружение активировано"

# Шаг 2: Обновление pip
print_info "Шаг 2/7: Обновление pip..."
pip install --upgrade pip --quiet
print_success "pip обновлен"

# Шаг 3: Установка зависимостей
print_info "Шаг 3/7: Установка зависимостей..."
print_warning "Это может занять несколько минут..."

pip install -r "$PROJECT_DIR/requirements.txt" --quiet || print_error "Не удалось установить зависимости"
print_success "Все зависимости установлены"

# Шаг 4: Настройка .env файла
print_info "Шаг 4/7: Настройка .env файла..."

if [ -f "$PROJECT_DIR/.env" ]; then
    print_warning "Файл .env уже существует"
    read -p "Пересоздать? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Пропускаем создание .env"
    else
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        print_success "Файл .env создан из шаблона"
    fi
else
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    print_success "Файл .env создан"
fi

# Запрос токена
print_warning "Необходимо настроить TELEGRAM_BOT_TOKEN"
echo -n "Введите ваш Telegram Bot Token (или нажмите Enter для настройки позже): "
read BOT_TOKEN

if [ ! -z "$BOT_TOKEN" ]; then
    # Замена токена в .env
    sed -i "s/your_bot_token_here/$BOT_TOKEN/g" "$PROJECT_DIR/.env"
    print_success "Токен сохранен в .env"
else
    print_warning "Не забудьте добавить токен в .env файл!"
    echo "  Используйте: nano $PROJECT_DIR/.env"
fi

# Установка прав доступа
chmod 600 "$PROJECT_DIR/.env"
print_success "Права доступа на .env установлены (600)"

# Шаг 5: Создание вспомогательных скриптов
print_info "Шаг 5/7: Создание вспомогательных скриптов..."

# Получаем username для PythonAnywhere
PA_USERNAME=$(whoami)

# Скрипт keep_alive.sh
cat > "$PROJECT_DIR/keep_alive.sh" << EOF
#!/bin/bash

PROJECT_DIR="$PROJECT_DIR"
VENV_PYTHON="\$PROJECT_DIR/venv/bin/python"
MAIN_SCRIPT="\$PROJECT_DIR/main.py"
PID_FILE="\$PROJECT_DIR/bot.pid"
LOG_FILE="\$PROJECT_DIR/bot.log"

is_running() {
    if [ -f "\$PID_FILE" ]; then
        PID=\$(cat "\$PID_FILE")
        if ps -p \$PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

if ! is_running; then
    echo "\$(date): Starting bot..." >> "\$LOG_FILE"
    cd "\$PROJECT_DIR"
    source venv/bin/activate
    nohup \$VENV_PYTHON \$MAIN_SCRIPT >> "\$LOG_FILE" 2>&1 &
    echo \$! > "\$PID_FILE"
    echo "\$(date): Bot started with PID \$(cat \$PID_FILE)" >> "\$LOG_FILE"
else
    echo "\$(date): Bot is already running" >> "\$LOG_FILE"
fi
EOF

chmod +x "$PROJECT_DIR/keep_alive.sh"
print_success "Создан keep_alive.sh"

# Скрипт status.sh
cat > "$PROJECT_DIR/status.sh" << EOF
#!/bin/bash

PID_FILE="$PROJECT_DIR/bot.pid"

if [ -f "\$PID_FILE" ]; then
    PID=\$(cat "\$PID_FILE")
    if ps -p \$PID > /dev/null 2>&1; then
        echo "✅ Bot is RUNNING (PID: \$PID)"
        echo "Uptime: \$(ps -p \$PID -o etime= | tr -d ' ')"
    else
        echo "❌ Bot is NOT RUNNING (stale PID file)"
    fi
else
    echo "❌ Bot is NOT RUNNING (no PID file)"
fi

echo ""
echo "Last 10 log lines:"
tail -10 $PROJECT_DIR/bot.log 2>/dev/null || echo "No logs yet"
EOF

chmod +x "$PROJECT_DIR/status.sh"
print_success "Создан status.sh"

# Скрипт stop.sh
cat > "$PROJECT_DIR/stop.sh" << EOF
#!/bin/bash

PID_FILE="$PROJECT_DIR/bot.pid"

if [ -f "\$PID_FILE" ]; then
    PID=\$(cat "\$PID_FILE")
    if ps -p \$PID > /dev/null 2>&1; then
        echo "Stopping bot (PID: \$PID)..."
        kill \$PID
        rm "\$PID_FILE"
        echo "✅ Bot stopped"
    else
        echo "Bot is not running (removing stale PID)"
        rm "\$PID_FILE"
    fi
else
    echo "Bot is not running"
fi
EOF

chmod +x "$PROJECT_DIR/stop.sh"
print_success "Создан stop.sh"

# Скрипт restart.sh
cat > "$PROJECT_DIR/restart.sh" << EOF
#!/bin/bash
$PROJECT_DIR/stop.sh
sleep 2
$PROJECT_DIR/keep_alive.sh
EOF

chmod +x "$PROJECT_DIR/restart.sh"
print_success "Создан restart.sh"

# Шаг 6: Создание алиасов
print_info "Шаг 6/7: Настройка алиасов..."

# Проверяем, есть ли уже алиасы
if grep -q "# Telegram Bot aliases" ~/.bashrc; then
    print_warning "Алиасы уже настроены в ~/.bashrc"
else
    cat >> ~/.bashrc << EOF

# Telegram Bot aliases
alias bot-status='$PROJECT_DIR/status.sh'
alias bot-start='$PROJECT_DIR/keep_alive.sh'
alias bot-stop='$PROJECT_DIR/stop.sh'
alias bot-restart='$PROJECT_DIR/restart.sh'
alias bot-logs='tail -f $PROJECT_DIR/bot.log'
alias bot-update='cd $PROJECT_DIR && git pull && bot-restart'
EOF
    print_success "Алиасы добавлены в ~/.bashrc"
fi

# Шаг 7: Финальная проверка
print_info "Шаг 7/7: Финальная проверка..."

# Проверка токена
if grep -q "your_bot_token_here" "$PROJECT_DIR/.env"; then
    print_warning "Токен бота НЕ настроен!"
    echo "  Отредактируйте файл: nano $PROJECT_DIR/.env"
else
    print_success "Токен бота настроен"
fi

# Проверка зависимостей
python -c "import telegram; from cryptography.hazmat.primitives.ciphers.aead import AESGCM" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "Зависимости установлены корректно"
else
    print_warning "Возможно, есть проблемы с зависимостями"
fi

# Итоговая информация
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Установка завершена успешно! 🎉           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

print_info "Следующие шаги:"
echo ""
echo "1. Настройте токен (если еще не сделали):"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Запустите бота:"
echo "   $PROJECT_DIR/keep_alive.sh"
echo ""
echo "   Или используйте алиас (после перезагрузки shell):"
echo "   source ~/.bashrc"
echo "   bot-start"
echo ""
echo "3. Проверьте статус:"
echo "   bot-status"
echo ""
echo "4. Просмотрите логи:"
echo "   bot-logs"
echo ""
echo "5. Настройте Scheduled Task в PythonAnywhere Dashboard:"
echo "   - Перейдите в Tasks"
echo "   - Добавьте: $PROJECT_DIR/keep_alive.sh"
echo "   - Частота: Hourly"
echo ""

print_info "Полная документация: $PROJECT_DIR/PYTHONANYWHERE.md"
echo ""

print_success "Готово! Удачи! 🚀"

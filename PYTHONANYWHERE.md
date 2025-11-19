# 🚀 Запуск бота на PythonAnywhere

Подробная пошаговая инструкция по развертыванию Telegram бота-шифровальщика на PythonAnywhere.

## 📋 Содержание

1. [Требования](#требования)
2. [Регистрация на PythonAnywhere](#регистрация)
3. [Клонирование репозитория](#клонирование)
4. [Настройка окружения](#настройка-окружения)
5. [Установка зависимостей](#установка-зависимостей)
6. [Настройка токена](#настройка-токена)
7. [Запуск бота](#запуск-бота)
8. [Автозапуск](#автозапуск)
9. [Мониторинг](#мониторинг)
10. [Troubleshooting](#troubleshooting)

---

## 📌 Требования

- Аккаунт на [PythonAnywhere](https://www.pythonanywhere.com)
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)
- Базовые знания Linux командной строки

### Ограничения бесплатного аккаунта:

✅ **Что работает:**
- Python 3.10/3.11
- Доступ к консоли Bash
- 512 MB дискового пространства
- Scheduled tasks (1 задача)
- Always-on tasks (платно, но можно использовать workaround)

⚠️ **Ограничения:**
- Нет Docker (будем запускать напрямую)
- Whitelist для внешних соединений (Telegram API разрешен)
- CPU time limits на бесплатном плане

---

## 🔐 Регистрация

### Шаг 1: Создайте аккаунт

1. Перейдите на [pythonanywhere.com](https://www.pythonanywhere.com)
2. Нажмите **"Start running Python online in less than a minute!"**
3. Выберите **Beginner** (бесплатный план)
4. Заполните форму регистрации
5. Подтвердите email

### Шаг 2: Получите Bot Token

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям (выберите имя и username)
4. Скопируйте токен (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. **Сохраните токен в безопасном месте!**

---

## 📥 Клонирование

### Шаг 1: Откройте Bash консоль

1. Войдите в [PythonAnywhere Dashboard](https://www.pythonanywhere.com/dashboard/)
2. Перейдите на вкладку **"Consoles"**
3. Нажмите **"Bash"** для создания новой консоли

### Шаг 2: Клонируйте репозиторий

```bash
# Перейдите в домашнюю директорию
cd ~

# Клонируйте репозиторий (замените URL на ваш)
git clone https://github.com/TovarishChekist/main.git telegram-bot
cd telegram-bot

# Проверьте содержимое
ls -la
```

**Альтернатива (если репозиторий приватный):**

```bash
# Загрузите код через Files tab в PythonAnywhere
# Или используйте wget/curl с публичным URL
```

---

## ⚙️ Настройка окружения

### Шаг 1: Создайте виртуальное окружение

```bash
# Создайте venv с Python 3.10
python3.10 -m venv venv

# Активируйте окружение
source venv/bin/activate

# Проверьте версию Python
python --version
# Должно показать: Python 3.10.x
```

### Шаг 2: Обновите pip

```bash
pip install --upgrade pip
```

---

## 📦 Установка зависимостей

### Шаг 1: Установите основные пакеты

```bash
# Активируйте venv если не активировано
source ~/telegram-bot/venv/bin/activate

# Установите зависимости
cd ~/telegram-bot
pip install -r requirements.txt
```

**Возможные проблемы:**

Если `stegano` не устанавливается:
```bash
# Установите системные зависимости (может потребовать времени)
pip install --no-cache-dir Pillow
pip install --no-cache-dir stegano
```

Если `argon2-cffi` дает ошибку:
```bash
pip install argon2-cffi --no-binary argon2-cffi
```

### Шаг 2: Проверьте установку

```bash
python -c "import telegram; print(telegram.__version__)"
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('OK')"
```

---

## 🔑 Настройка токена

### Вариант 1: Через .env файл (рекомендуется)

```bash
cd ~/telegram-bot

# Создайте .env из примера
cp .env.example .env

# Отредактируйте файл
nano .env
```

В редакторе `nano`:
1. Замените `your_bot_token_here` на ваш реальный токен
2. Нажмите `Ctrl+O` для сохранения
3. Нажмите `Enter` для подтверждения
4. Нажмите `Ctrl+X` для выхода

**Пример .env:**
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
LOG_LEVEL=INFO
MAX_REQUESTS_PER_MINUTE=30
MAX_REQUESTS_PER_HOUR=500
```

### Вариант 2: Через environment variables (более безопасно)

```bash
# Добавьте в ~/.bashrc
echo 'export TELEGRAM_BOT_TOKEN="ваш_токен_здесь"' >> ~/.bashrc

# Перезагрузите конфигурацию
source ~/.bashrc

# Проверьте
echo $TELEGRAM_BOT_TOKEN
```

---

## 🚀 Запуск бота

### Тестовый запуск

```bash
# Активируйте venv
source ~/telegram-bot/venv/bin/activate

# Перейдите в директорию
cd ~/telegram-bot

# Запустите бота
python main.py
```

**Ожидаемый вывод:**
```
2024-01-15 10:30:00 - __main__ - INFO - Starting Advanced Telegram Encryption Bot...
2024-01-15 10:30:01 - __main__ - INFO - Bot initialized successfully
2024-01-15 10:30:01 - __main__ - INFO - Security features enabled:
2024-01-15 10:30:01 - __main__ - INFO -   ✓ AES-256-GCM encryption
2024-01-15 10:30:01 - __main__ - INFO -   ✓ ChaCha20-Poly1305 encryption
...
2024-01-15 10:30:02 - __main__ - INFO - Starting polling...
```

### Проверка работы

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте `/start`
4. Бот должен ответить приветственным сообщением

**Если все работает, нажмите `Ctrl+C` для остановки.**

---

## 🔄 Автозапуск

### Вариант 1: Always-On Task (платная функция)

Если у вас платный аккаунт:

1. Перейдите в **Dashboard → Tasks**
2. В разделе **Always-on tasks** нажмите **Add a new always-on task**
3. Укажите:
   ```
   Working directory: /home/yourusername/telegram-bot
   Command: /home/yourusername/telegram-bot/venv/bin/python main.py
   ```

### Вариант 2: Scheduled Task + Keeper Script (бесплатно)

Создайте скрипт для автоматического перезапуска:

#### Шаг 1: Создайте keeper скрипт

```bash
nano ~/telegram-bot/keep_alive.sh
```

Содержимое:
```bash
#!/bin/bash

# Путь к проекту
PROJECT_DIR="/home/yourusername/telegram-bot"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
PID_FILE="$PROJECT_DIR/bot.pid"
LOG_FILE="$PROJECT_DIR/bot.log"

# Функция для проверки, запущен ли бот
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Если бот не запущен, запускаем его
if ! is_running; then
    echo "$(date): Starting bot..." >> "$LOG_FILE"

    cd "$PROJECT_DIR"
    source venv/bin/activate

    nohup $VENV_PYTHON $MAIN_SCRIPT >> "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "$(date): Bot started with PID $(cat $PID_FILE)" >> "$LOG_FILE"
else
    echo "$(date): Bot is already running" >> "$LOG_FILE"
fi
```

**Замените `yourusername` на ваше имя пользователя!**

```bash
# Сделайте скрипт исполняемым
chmod +x ~/telegram-bot/keep_alive.sh

# Замените yourusername
sed -i 's/yourusername/ВАШ_USERNAME/g' ~/telegram-bot/keep_alive.sh
```

#### Шаг 2: Настройте Scheduled Task

1. Перейдите в **Dashboard → Tasks**
2. В разделе **Scheduled tasks** добавьте новую задачу:
   - **Frequency:** Hourly (или каждые несколько часов)
   - **Command:** `/home/yourusername/telegram-bot/keep_alive.sh`
3. Нажмите **Create**

#### Шаг 3: Первый запуск

```bash
# Запустите keeper скрипт вручную
~/telegram-bot/keep_alive.sh

# Проверьте логи
tail -f ~/telegram-bot/bot.log
```

### Вариант 3: tmux/screen сессия

```bash
# Установите tmux (если еще нет)
pip install --user tmux

# Создайте новую сессию
tmux new -s telegram-bot

# Внутри tmux запустите бота
cd ~/telegram-bot
source venv/bin/activate
python main.py

# Отключитесь от сессии: Ctrl+B, затем D

# Подключитесь обратно
tmux attach -t telegram-bot

# Завершите сессию
tmux kill-session -t telegram-bot
```

---

## 📊 Мониторинг

### Проверка статуса бота

```bash
# Проверьте, запущен ли процесс
ps aux | grep "python main.py"

# Проверьте PID файл
cat ~/telegram-bot/bot.pid

# Просмотрите логи
tail -50 ~/telegram-bot/bot.log

# Следите за логами в реальном времени
tail -f ~/telegram-bot/bot.log
```

### Создайте скрипт для статуса

```bash
nano ~/telegram-bot/status.sh
```

Содержимое:
```bash
#!/bin/bash

PID_FILE="/home/yourusername/telegram-bot/bot.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Bot is RUNNING (PID: $PID)"
        echo "Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
    else
        echo "❌ Bot is NOT RUNNING (stale PID file)"
    fi
else
    echo "❌ Bot is NOT RUNNING (no PID file)"
fi

echo ""
echo "Last 10 log lines:"
tail -10 /home/yourusername/telegram-bot/bot.log
```

```bash
chmod +x ~/telegram-bot/status.sh
sed -i 's/yourusername/ВАШ_USERNAME/g' ~/telegram-bot/status.sh

# Использование
~/telegram-bot/status.sh
```

### Остановка бота

```bash
nano ~/telegram-bot/stop.sh
```

Содержимое:
```bash
#!/bin/bash

PID_FILE="/home/yourusername/telegram-bot/bot.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping bot (PID: $PID)..."
        kill $PID
        rm "$PID_FILE"
        echo "✅ Bot stopped"
    else
        echo "Bot is not running (removing stale PID)"
        rm "$PID_FILE"
    fi
else
    echo "Bot is not running"
fi
```

```bash
chmod +x ~/telegram-bot/stop.sh
sed -i 's/yourusername/ВАШ_USERNAME/g' ~/telegram-bot/stop.sh
```

### Перезапуск бота

```bash
# Создайте скрипт перезапуска
echo '#!/bin/bash
~/telegram-bot/stop.sh
sleep 2
~/telegram-bot/keep_alive.sh
' > ~/telegram-bot/restart.sh

chmod +x ~/telegram-bot/restart.sh
```

---

## 🛠️ Troubleshooting

### Проблема 1: "ModuleNotFoundError"

**Ошибка:**
```
ModuleNotFoundError: No module named 'telegram'
```

**Решение:**
```bash
# Убедитесь, что venv активирован
source ~/telegram-bot/venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt

# Проверьте, что используете правильный Python
which python
# Должно показать: /home/yourusername/telegram-bot/venv/bin/python
```

### Проблема 2: "Token is invalid"

**Ошибка:**
```
telegram.error.InvalidToken: Invalid token
```

**Решение:**
```bash
# Проверьте токен в .env
cat ~/telegram-bot/.env | grep TOKEN

# Убедитесь, что нет лишних пробелов или кавычек
# Правильно: TELEGRAM_BOT_TOKEN=123456789:ABC...
# Неправильно: TELEGRAM_BOT_TOKEN="123456789:ABC..."

# Переустановите токен
nano ~/telegram-bot/.env
```

### Проблема 3: Бот не отвечает

**Проверьте:**

1. **Запущен ли бот:**
   ```bash
   ~/telegram-bot/status.sh
   ```

2. **Логи на ошибки:**
   ```bash
   tail -50 ~/telegram-bot/bot.log | grep -i error
   ```

3. **Network connectivity:**
   ```bash
   curl -s https://api.telegram.org/botYOUR_TOKEN/getMe
   ```

4. **Перезапустите бота:**
   ```bash
   ~/telegram-bot/restart.sh
   ```

### Проблема 4: "Memory limit exceeded"

**Ошибка:**
```
MemoryError
```

**Решение:**

1. **Оптимизируйте код:**
   - Ограничьте размер кэша сессий
   - Используйте ленивую загрузку

2. **Очистите память:**
   ```bash
   # Перезапустите бота
   ~/telegram-bot/restart.sh
   ```

3. **Upgrade на платный план** (больше RAM)

### Проблема 5: "CPU limit exceeded"

**Ошибка:**
```
Your account's CPU usage is too high
```

**Решение:**

1. **Используйте webhook вместо polling** (более эффективно)
2. **Оптимизируйте криптографические операции**
3. **Добавьте кэширование**
4. **Upgrade на платный план**

### Проблема 6: Бот останавливается сам

**Причины:**
- PythonAnywhere убивает long-running процессы на бесплатном плане
- Ошибка в коде
- Network timeout

**Решение:**

1. **Используйте keeper скрипт** (см. выше)
2. **Добавьте error handling:**
   ```python
   # В main.py
   while True:
       try:
           application.run_polling()
       except Exception as e:
           logger.error(f"Bot crashed: {e}")
           time.sleep(5)
   ```

3. **Проверяйте логи регулярно**

---

## 🔒 Безопасность на PythonAnywhere

### 1. Защита токена

```bash
# Установите правильные права на .env
chmod 600 ~/telegram-bot/.env

# Проверьте
ls -la ~/telegram-bot/.env
# Должно быть: -rw------- (только владелец может читать/писать)
```

### 2. Регулярные обновления

```bash
# Обновляйте код
cd ~/telegram-bot
git pull

# Обновляйте зависимости
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Перезапускайте бота
~/telegram-bot/restart.sh
```

### 3. Мониторинг логов

```bash
# Проверяйте на подозрительную активность
grep -i "blocked\|suspicious\|failed" ~/telegram-bot/bot.log
```

### 4. Ротация логов

```bash
# Создайте скрипт для ротации
nano ~/telegram-bot/rotate_logs.sh
```

Содержимое:
```bash
#!/bin/bash

LOG_FILE="/home/yourusername/telegram-bot/bot.log"
MAX_SIZE=10485760  # 10 MB

if [ -f "$LOG_FILE" ]; then
    SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE")
    if [ $SIZE -gt $MAX_SIZE ]; then
        mv "$LOG_FILE" "$LOG_FILE.old"
        touch "$LOG_FILE"
        echo "Log rotated at $(date)" >> "$LOG_FILE"
    fi
fi
```

```bash
chmod +x ~/telegram-bot/rotate_logs.sh
```

---

## 📱 Полезные команды

### Быстрая справка

```bash
# Статус бота
~/telegram-bot/status.sh

# Запуск бота
~/telegram-bot/keep_alive.sh

# Остановка бота
~/telegram-bot/stop.sh

# Перезапуск бота
~/telegram-bot/restart.sh

# Просмотр логов
tail -f ~/telegram-bot/bot.log

# Проверка токена
grep TOKEN ~/telegram-bot/.env

# Обновление кода
cd ~/telegram-bot && git pull && ~/telegram-bot/restart.sh
```

### Создайте алиасы

```bash
# Добавьте в ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# Telegram Bot aliases
alias bot-status='~/telegram-bot/status.sh'
alias bot-start='~/telegram-bot/keep_alive.sh'
alias bot-stop='~/telegram-bot/stop.sh'
alias bot-restart='~/telegram-bot/restart.sh'
alias bot-logs='tail -f ~/telegram-bot/bot.log'
alias bot-update='cd ~/telegram-bot && git pull && bot-restart'

EOF

# Применить изменения
source ~/.bashrc

# Теперь можно использовать просто:
bot-status
bot-logs
```

---

## 🎯 Рекомендации

### Для бесплатного плана:

1. ✅ Используйте keeper скрипт для автоматического перезапуска
2. ✅ Настройте Scheduled Task на каждый час
3. ✅ Регулярно проверяйте логи
4. ✅ Используйте tmux для интерактивного дебага
5. ⚠️ Будьте готовы к остановкам (PythonAnywhere ограничения)

### Для платного плана:

1. ✅ Используйте Always-On Task
2. ✅ Включите больше RAM для стабильности
3. ✅ Настройте email уведомления при падении
4. ✅ Используйте webhook вместо polling (эффективнее)

### Оптимизация производительности:

```python
# В main.py, добавьте конфигурацию для polling
application = Application.builder().token(token).build()

# Оптимизированные настройки polling
application.run_polling(
    poll_interval=1.0,  # Проверка каждую секунду
    timeout=10,          # Timeout для запросов
    drop_pending_updates=True  # Игнорировать старые обновления при запуске
)
```

---

## 📞 Поддержка

**Если что-то не работает:**

1. Проверьте логи: `tail -50 ~/telegram-bot/bot.log`
2. Проверьте статус: `~/telegram-bot/status.sh`
3. Прочитайте [PythonAnywhere Help](https://help.pythonanywhere.com/)
4. Проверьте [Telegram Bot API Status](https://www.githubstatus.com/)

**Полезные ссылки:**

- [PythonAnywhere Forums](https://www.pythonanywhere.com/forums/)
- [PythonAnywhere Help](https://help.pythonanywhere.com/)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)

---

## ✅ Checklist после установки

- [ ] Репозиторий клонирован
- [ ] Виртуальное окружение создано и активировано
- [ ] Все зависимости установлены
- [ ] .env файл создан с правильным токеном
- [ ] Бот запускается без ошибок
- [ ] Бот отвечает в Telegram на `/start`
- [ ] Keeper скрипт создан и работает
- [ ] Scheduled Task настроен
- [ ] Логи пишутся корректно
- [ ] Права доступа на файлы настроены (600 для .env)

**Поздравляю! Ваш бот-шифровальщик запущен на PythonAnywhere! 🎉**

---

**Совет:** Bookmark эту инструкцию для быстрого доступа к командам!

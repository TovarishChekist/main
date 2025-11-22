# Деплой на PythonAnywhere

## Важная информация

PythonAnywhere имеет ограничения для бесплатных аккаунтов:
- **Long polling не работает** (требуется always-on task - только в платных планах)
- Нужно использовать **webhook** вместо polling
- Доступен только HTTPS (что подходит для Telegram webhooks)

## Вариант 1: Webhook (рекомендуется для PythonAnywhere)

### Шаг 1: Регистрация на PythonAnywhere

1. Зарегистрируйтесь на https://www.pythonanywhere.com
2. Выберите бесплатный план (Beginner account)

### Шаг 2: Загрузка кода

1. Откройте Bash консоль в PythonAnywhere
2. Клонируйте репозиторий:
```bash
git clone https://github.com/TovarishChekist/main.git
cd main
git checkout claude/telegram-encryption-bot-01Dj6hg3bpPTguqT2ehgq3rc
```

### Шаг 3: Установка зависимостей

1. Создайте виртуальное окружение:
```bash
mkvirtualenv --python=/usr/bin/python3.10 telegram-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
pip install aiohttp
```

### Шаг 4: Настройка Web App

1. Перейдите в раздел "Web" на PythonAnywhere
2. Нажмите "Add a new web app"
3. Выберите "Manual configuration"
4. Выберите Python 3.10

### Шаг 5: Настройка WSGI файла

1. Откройте WSGI configuration file (путь будет показан на странице Web)
2. Замените содержимое на код из `webhook_bot.py` (создам ниже)

### Шаг 6: Настройка переменных окружения

1. В PythonAnywhere перейдите в Files → создайте `.env` файл
2. Добавьте:
```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
WEBHOOK_URL=https://ваш-username.pythonanywhere.com/webhook
```

### Шаг 7: Настройка webhook

1. Замените в `webhook_bot.py` URL на ваш
2. Перезагрузите web app
3. Webhook автоматически установится при первом запросе

### Шаг 8: Проверка

1. Откройте Telegram и найдите вашего бота
2. Отправьте /start
3. Если не работает, проверьте:
   - Error log в разделе Web
   - Server log в разделе Web
   - Что webhook установлен: https://api.telegram.org/bot{TOKEN}/getWebhookInfo

## Вариант 2: Запуск на VPS/своем сервере

Если у вас есть свой сервер или VPS (например, Digital Ocean, AWS, etc.):

### 1. Установка зависимостей
```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

### 2. Клонирование репозитория
```bash
git clone https://github.com/TovarishChekist/main.git
cd main
git checkout claude/telegram-encryption-bot-01Dj6hg3bpPTguqT2ehgq3rc
```

### 3. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Настройка .env
```bash
cp .env.example .env
nano .env  # добавьте токен
```

### 5. Запуск бота
```bash
python bot.py
```

### 6. Запуск в фоне (systemd)

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Encryption Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/main
Environment="PATH=/path/to/main/venv/bin"
ExecStart=/path/to/main/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Вариант 3: Heroku

1. Установите Heroku CLI
2. Создайте `Procfile`:
```
worker: python bot.py
```

3. Деплой:
```bash
heroku login
heroku create ваше-имя-бота
git push heroku main
heroku ps:scale worker=1
```

## Вариант 4: Docker

Используйте `Dockerfile` (создам ниже)

```bash
docker build -t telegram-bot .
docker run -d --env-file .env telegram-bot
```

## Решение проблем

### Бот не отвечает
- Проверьте токен в .env
- Проверьте логи: `tail -f logs/bot.log`
- Убедитесь, что бот запущен: `ps aux | grep bot.py`

### Ошибки с cryptography
```bash
pip install --upgrade cryptography
```

### Недостаточно памяти на PythonAnywhere
- Используйте webhook вместо polling
- Ограничьте размер файлов для шифрования

### Проблемы с базой данных
- Проверьте права на запись: `chmod 666 keys.db`
- Проверьте наличие .master_key файла

## Безопасность

1. **Никогда не коммитьте** `.env`, `keys.db`, `.master_key` в git
2. **Регулярно делайте бэкап** .master_key и keys.db
3. **Используйте HTTPS** для webhook
4. **Ограничьте доступ** к серверу файрволом

## Мониторинг

Проверка статуса webhook:
```bash
curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo
```

Просмотр логов:
```bash
tail -f /var/log/telegram-bot/bot.log
```

## Производительность

Для PythonAnywhere бесплатного плана:
- Ограничение: 100 секунд CPU/день
- Рекомендуется: использовать webhook
- Избегайте: тяжелых операций RSA для каждого сообщения

## Дополнительные ресурсы

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram документация](https://docs.aiogram.dev/)
- [PythonAnywhere Help](https://help.pythonanywhere.com/)

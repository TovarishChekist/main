# Руководство по развертыванию бота

## Развертывание на сервере Linux

### 1. Подготовка сервера

Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

Установите необходимые пакеты:
```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### 2. Клонирование проекта

```bash
cd /opt  # или другая директория
git clone <repository_url> telegram_bot
cd telegram_bot
```

### 3. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполните все необходимые параметры в файле `.env`.

### 6. Тестовый запуск

```bash
python bot.py
```

Убедитесь, что бот запускается без ошибок. Нажмите Ctrl+C для остановки.

## Автозапуск через systemd

### 1. Создание сервиса

Отредактируйте файл `telegram-bot.service`:

```bash
nano telegram-bot.service
```

Замените:
- `your_username` на имя вашего пользователя
- `/path/to/telegram_bot` на полный путь к проекту

### 2. Копирование сервиса

```bash
sudo cp telegram-bot.service /etc/systemd/system/
```

### 3. Перезагрузка systemd

```bash
sudo systemctl daemon-reload
```

### 4. Включение автозапуска

```bash
sudo systemctl enable telegram-bot.service
```

### 5. Запуск сервиса

```bash
sudo systemctl start telegram-bot.service
```

### 6. Проверка статуса

```bash
sudo systemctl status telegram-bot.service
```

## Управление сервисом

### Остановка бота
```bash
sudo systemctl stop telegram-bot.service
```

### Перезапуск бота
```bash
sudo systemctl restart telegram-bot.service
```

### Просмотр логов
```bash
sudo journalctl -u telegram-bot.service -f
```

### Просмотр последних 100 строк логов
```bash
sudo journalctl -u telegram-bot.service -n 100
```

## Обновление бота

### 1. Остановка сервиса
```bash
sudo systemctl stop telegram-bot.service
```

### 2. Получение обновлений
```bash
cd /opt/telegram_bot
git pull origin main
```

### 3. Обновление зависимостей
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 4. Запуск сервиса
```bash
sudo systemctl start telegram-bot.service
```

## Мониторинг

### Проверка работы бота
```bash
sudo systemctl is-active telegram-bot.service
```

### Автоматический перезапуск при падении

Сервис настроен на автоматический перезапуск (параметр `Restart=always` в файле сервиса).

### Ротация логов

Логи хранятся в `logs/bot.log`. Рекомендуется настроить logrotate:

Создайте файл `/etc/logrotate.d/telegram-bot`:

```
/opt/telegram_bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_username your_username
}
```

## Безопасность

### 1. Права доступа

Установите корректные права на файлы:

```bash
chmod 600 .env
chmod 755 bot.py
chmod 755 start.sh
```

### 2. Firewall

Убедитесь, что исходящие соединения к Telegram API разрешены:

```bash
sudo ufw allow out 443/tcp
sudo ufw allow out 80/tcp
```

### 3. Резервное копирование

Регулярно создавайте бэкапы:

```bash
# Бэкап конфигурации
cp .env .env.backup

# Бэкап логов
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u telegram-bot.service -n 50
   ```

2. Проверьте права доступа:
   ```bash
   ls -la /opt/telegram_bot
   ```

3. Проверьте конфигурацию:
   ```bash
   cat .env
   ```

### Бот запускается, но не отвечает

1. Проверьте интернет-соединение:
   ```bash
   ping api.telegram.org
   ```

2. Проверьте корректность токена в `.env`

3. Проверьте логи бота в `logs/bot.log`

### Высокое потребление ресурсов

1. Проверьте использование памяти:
   ```bash
   sudo systemctl status telegram-bot.service
   ```

2. Проверьте размер логов:
   ```bash
   du -sh logs/
   ```

## Развертывание в Docker (опционально)

### Dockerfile

Создайте файл `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram-bot
    restart: always
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

### Запуск

```bash
docker-compose up -d
```

## Контакты

По вопросам развертывания обращайтесь к администраторам проекта.

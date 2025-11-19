# Развертывание бота на PythonAnywhere

Пошаговая инструкция по запуску Telegram бота на хостинге PythonAnywhere.

## Важно: Требования к аккаунту

⚠️ **Для запуска Telegram бота на PythonAnywhere требуется платный аккаунт!**

- **Бесплатный аккаунт** — не подходит (нет always-on tasks)
- **Hacker Plan ($5/месяц)** — подходит для небольших ботов
- **Web Developer и выше** — рекомендуется для продакшена

Бесплатный аккаунт позволяет только запускать scheduled tasks (по расписанию), но не постоянно работающие процессы.

## Шаг 1: Регистрация на PythonAnywhere

1. Перейдите на [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Нажмите "Start running Python online in less than a minute"
3. Выберите тарифный план (минимум Hacker для бота)
4. Зарегистрируйтесь

## Шаг 2: Загрузка кода

### Вариант 1: Через Git (рекомендуется)

1. Откройте **Bash console** в PythonAnywhere
2. Клонируйте репозиторий:

```bash
git clone https://github.com/ваш-username/ваш-репозиторий.git
cd ваш-репозиторий
```

### Вариант 2: Загрузка через Files

1. Перейдите в раздел **Files**
2. Создайте директорию для бота (например, `telegram-bot`)
3. Загрузите все файлы проекта через интерфейс

## Шаг 3: Создание виртуального окружения

В **Bash console**:

```bash
# Переходим в директорию проекта
cd ~/ваш-репозиторий

# Создаём виртуальное окружение
python3.10 -m venv venv

# Активируем окружение
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости
pip install -r requirements.txt
```

## Шаг 4: Настройка переменных окружения

1. Создайте файл `.env` в директории проекта:

```bash
nano .env
```

2. Добавьте настройки:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_telegram_id
```

3. Сохраните файл (Ctrl+O, Enter, Ctrl+X)

## Шаг 5: Проверка работы бота

Протестируйте бота вручную:

```bash
source venv/bin/activate
python bot.py
```

Если бот запустился без ошибок, нажмите Ctrl+C для остановки.

## Шаг 6: Настройка Always-On Task

1. Перейдите в раздел **Tasks** на панели PythonAnywhere
2. В секции **Always-on tasks** нажмите **Create a new always-on task**
3. Заполните поля:
   - **Description**: `Telegram Appeals Bot`
   - **Command**: `/home/ваш_username/ваш-репозиторий/venv/bin/python /home/ваш_username/ваш-репозиторий/bot.py`
   - **Working directory**: `/home/ваш_username/ваш-репозиторий`

4. Нажмите **Create**
5. Включите задачу кнопкой **Enable**

### Пример команды

Если ваш username `myuser` и репозиторий `telegram-bot`:

```bash
/home/myuser/telegram-bot/venv/bin/python /home/myuser/telegram-bot/bot.py
```

## Шаг 7: Мониторинг

### Просмотр логов

1. Перейдите в раздел **Tasks**
2. Найдите вашу задачу
3. Нажмите **Log** для просмотра логов

### Проверка статуса

- Зелёная галочка ✓ — бот работает
- Красный крестик ✗ — бот остановлен или произошла ошибка

### Перезапуск бота

1. Нажмите **Stop** для остановки
2. Подождите несколько секунд
3. Нажмите **Start** для запуска

## Альтернатива: Scheduled Task (для бесплатного аккаунта)

⚠️ Этот метод **НЕ рекомендуется** для ботов, так как они будут работать только по расписанию!

Но если у вас бесплатный аккаунт:

1. Перейдите в **Tasks** → **Scheduled**
2. Создайте задачу, которая запускается каждый час:
   - Hour: `*` (каждый час)
   - Minute: `0` (в начале часа)
   - Command: `/home/username/telegram-bot/venv/bin/python /home/username/telegram-bot/bot.py`

**Проблемы этого подхода:**
- Бот работает только 1 раз в час
- Время работы ограничено
- Не подходит для реального использования

## Обновление бота

Когда нужно обновить код:

```bash
# В Bash console
cd ~/ваш-репозиторий

# Получаем изменения
git pull origin main

# Активируем окружение
source venv/bin/activate

# Обновляем зависимости (если изменились)
pip install -r requirements.txt
```

Затем перезапустите Always-On Task через панель Tasks.

## Автоматическое обновление через скрипт

Создайте файл `update.sh`:

```bash
#!/bin/bash
cd ~/telegram-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
echo "Bot updated! Restart the Always-On Task manually."
```

Сделайте исполняемым:

```bash
chmod +x update.sh
```

Запускайте для обновления:

```bash
./update.sh
```

## Проверка работы

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Проверьте, что бот отвечает
4. Попробуйте подать тестовое обращение

## Решение проблем

### Бот не запускается

1. Проверьте логи в разделе Tasks
2. Убедитесь, что токен бота правильный
3. Проверьте права доступа к файлам
4. Убедитесь, что виртуальное окружение активировано

### Ошибка "ModuleNotFoundError"

Переустановите зависимости:

```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### База данных не создаётся

Проверьте права на запись:

```bash
chmod 755 ~/ваш-репозиторий
```

### Бот постоянно падает

1. Проверьте логи
2. Убедитесь, что токен валиден
3. Проверьте интернет-соединение PythonAnywhere
4. Обратитесь в поддержку PythonAnywhere

## Мониторинг и уведомления

Для автоматического мониторинга можно использовать:

- **UptimeRobot** — проверка доступности
- **Dead Man's Snitch** — проверка что бот живой
- Встроенные логи PythonAnywhere

## Безопасность

1. **Никогда** не коммитьте файл `.env` в Git
2. Используйте переменные окружения для секретов
3. Регулярно обновляйте зависимости
4. Ограничьте доступ к консоли PythonAnywhere

## Стоимость

**Hacker Plan** ($5/месяц):
- 1 always-on task ✓
- 100,000 CPU секунд/день
- Достаточно для бота с небольшой нагрузкой

**Web Developer** ($12/месяц):
- 2 always-on tasks
- 2,000,000 CPU секунд/день
- Рекомендуется для активных ботов

## Полезные команды

```bash
# Проверить процессы
ps aux | grep python

# Проверить использование диска
du -sh ~/telegram-bot

# Просмотр последних логов
tail -f /path/to/logs

# Проверить версию Python
python --version

# Список установленных пакетов
pip list
```

## Альтернативные хостинги

Если PythonAnywhere не подходит, рассмотрите:

- **Heroku** (есть бесплатный план)
- **Railway** (бесплатный план с ограничениями)
- **Render** (бесплатный план)
- **DigitalOcean** ($4/месяц за VPS)
- **AWS EC2** (free tier 12 месяцев)

## Поддержка

При возникновении проблем:
1. Проверьте логи PythonAnywhere
2. Изучите документацию: [https://help.pythonanywhere.com](https://help.pythonanywhere.com)
3. Форум PythonAnywhere: [https://www.pythonanywhere.com/forums/](https://www.pythonanywhere.com/forums/)

---

**Готово!** Ваш бот запущен на PythonAnywhere и работает 24/7 🚀

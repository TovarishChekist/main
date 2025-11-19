# ⚡ Быстрый старт на PythonAnywhere

## 5 минут до запуска бота! 🚀

### Шаг 1: Получите Bot Token (1 минута)

1. Откройте Telegram, найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Дайте имя боту (например: "My Encryption Bot")
4. Дайте username (например: "my_encryption_bot")
5. **Скопируйте токен** (выглядит как `123456789:ABCdefGHI...`)

### Шаг 2: Зарегистрируйтесь на PythonAnywhere (1 минута)

1. Перейдите на [pythonanywhere.com](https://www.pythonanywhere.com)
2. Нажмите "Start running Python online"
3. Выберите **Beginner** (бесплатно)
4. Заполните форму регистрации

### Шаг 3: Установите бота (2 минуты)

1. В PythonAnywhere Dashboard откройте **Bash Console**

2. Выполните команды:

```bash
# Клонируйте репозиторий
git clone https://github.com/ВАШ_USERNAME/telegram-bot.git telegram-bot
cd telegram-bot

# Запустите автоматическую установку
./setup_pythonanywhere.sh
```

3. Когда скрипт попросит токен, вставьте его:
```
Введите ваш Telegram Bot Token: 123456789:ABCdefGHI...
```

4. Дождитесь завершения установки

### Шаг 4: Запустите бота (30 секунд)

```bash
# Запустите бота
./keep_alive.sh

# Проверьте статус
./status.sh
```

### Шаг 5: Настройте автозапуск (30 секунд)

1. Перейдите в **Dashboard → Tasks**
2. В разделе **Scheduled tasks** нажмите **Add a new task**
3. Настройте:
   - **Hour:** Оставьте пустым (каждый час)
   - **Minute:** 0
   - **Command:** `/home/ВАШЕ_ИМЯ/telegram-bot/keep_alive.sh`
4. Нажмите **Create**

**Замените `ВАШЕ_ИМЯ` на ваш username в PythonAnywhere!**

---

## ✅ Готово!

Откройте Telegram и найдите вашего бота:
```
/start
```

Бот должен ответить приветственным сообщением! 🎉

---

## 🔧 Полезные команды

После установки вы можете использовать:

```bash
# Перезагрузить shell для использования алиасов
source ~/.bashrc

# Статус бота
bot-status

# Остановить бота
bot-stop

# Перезапустить бота
bot-restart

# Смотреть логи
bot-logs

# Обновить код
bot-update
```

---

## 📚 Дополнительная информация

- **Полная документация:** [PYTHONANYWHERE.md](PYTHONANYWHERE.md)
- **Руководство по безопасности:** [SECURITY.md](SECURITY.md)
- **Примеры использования:** [EXAMPLES.md](EXAMPLES.md)

---

## 🆘 Что-то не работает?

### Проблема: Бот не отвечает

```bash
# Проверьте статус
./status.sh

# Проверьте логи на ошибки
tail -50 bot.log

# Перезапустите
./restart.sh
```

### Проблема: "Invalid token"

```bash
# Проверьте токен в .env
cat .env | grep TOKEN

# Отредактируйте если нужно
nano .env
```

### Проблема: Бот останавливается

**Решение:** Scheduled Task будет автоматически перезапускать его каждый час!

---

## 💡 Совет

Добавьте в закладки команду для быстрого доступа к консоли:
```
https://www.pythonanywhere.com/user/ВАШ_USERNAME/consoles/
```

---

**Наслаждайтесь безопасным шифрованием! 🔐**

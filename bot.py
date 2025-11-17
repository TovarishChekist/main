# -*- coding: utf-8 -*-

import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import telebot.apihelper as apihelper
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Настройки таймаутов для стабильной работы
apihelper.CONNECT_TIMEOUT = 15.0  # Таймаут подключения
apihelper.READ_TIMEOUT = 15.0     # Таймаут чтения ответа

# Опционально: настройка прокси (раскомментируйте при необходимости)
# apihelper.proxy = {'https': 'socks5://localhost:9050'}

# Конфигурация бота из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')
APPEAL_CHAT_ID = int(os.getenv('APPEAL_CHAT_ID', '-1002863620257'))
APPLICATION_CHAT_ID = int(os.getenv('APPLICATION_CHAT_ID', '-1002692926810'))

# Проверка наличия токена
if not TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    raise ValueError("BOT_TOKEN не установлен. Создайте файл .env с токеном бота.")

# Текст информации о Совете
COUNCIL_INFO = """
🌟 <b>Привет, будущий лидер!</b> 🌟

Мы — <b>Детский и Молодёжный Общественный Совет</b> при Уполномоченном по правам ребёнка в Амурской области! 🏛️✨

Это твоя площадка для реальных изменений! 💪 Мы — команда активных ребят, которая помогает решать важные вопросы, касающиеся всех детей и подростков!

🎯 <b>Наша миссия — сделать твой голос слышимым!</b>

🔥 <b>Что мы делаем:</b>

🌍 <b>Меняем мир вместе!</b> — Привлекаем детей и молодёжь к участию в общественной жизни, ведь именно ты можешь сделать наш регион лучше!

📚 <b>Прокачиваем твои знания!</b> — Помогаем разобраться в правах человека и формируем активную гражданскую позицию. 💡

💬 <b>Даем право голоса!</b> — Создаем возможности для каждого ребенка свободно выражать свои мысли по всем важным вопросам. Твое мнение важно! 🎤

⚙️ <b>Влияем на решения!</b> — Разрабатываем реальные механизмы участия детей в принятии решений на всех уровнях власти! 🏢

🚀 <b>Почему стоит к нам присоединиться? С нами ты:</b>

✅ Развиваешь <b>лидерские качества</b>
✅ Находишь <b>единомышленников</b>
✅ Участвуешь в <b>реальных проектах</b>
✅ Влияешь на <b>жизнь в регионе</b>
✅ Получаешь <b>уникальный опыт</b>

<b>Готов стать частью нашей команды?</b> 🔥
"""

# Текст информации о Руководстве Совета
LEADERSHIP_INFO = """
📌Кадыханова Светлана – Куратор Совета

📌Гип Евгений – Председатель Совета

📌Герасименко Мария – Заместитель председателя Совета

📌Рыбаков Тарас – Руководитель проектного отдела

📌Хайлова Вероника – Руководитель Пресс-службы

📌Косянюк Илья – Ответственный секретарь
"""

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Словари для хранения состояний и данных пользователей
user_states = {}  # chat_id -> состояние
user_data = {}    # chat_id -> данные заявки
responses_map = {}  # (group_chat_id, group_message_id) -> user_chat_id
last_bot_message = {}  # chat_id -> message_id последнего сообщения бота


def main_menu():
    """Создание основного меню с кнопками"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("📩 Обращение в Совет"))
    markup.add(KeyboardButton("📝 Заявка на вступление в Совет"))
    markup.add(KeyboardButton("ℹ️ Информация о Совете"))
    markup.add(KeyboardButton("👥 Руководство Совета"))
    return markup


def back_to_menu():
    """Создание кнопки 'Вернуться в меню'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Вернуться в меню"))
    return markup


def send_menu(chat_id, text=None):
    """Отправка главного меню пользователю"""
    if text is None:
        text = """<b>🌟 Добро пожаловать в официальный бот Детского и Молодёжного Общественного Совета при Уполномоченном по правам ребёнка в Амурской области! 🌟</b>

Ты попал в место, где твой голос имеет значение! 🗣️ Здесь ты можешь:

🔹 <b>Обратиться в Совет</b> — поделиться проблемой или предложением
🔹 <b>Подать заявку на вступление</b> — стать частью команды активных ребят
🔹 <b>Узнать больше о нашей работе</b> — познакомиться с целями и задачами Совета
🔹 <b>Посмотреть состав руководства</b> — увидеть, кто управляет Советом

Мы работаем для защиты прав детей и молодёжи в Амурской области. Присоединяйся к нам и делай мир лучше! 🚀

<b>Выбери действие:</b> 👇"""

    try:
        sent = bot.send_message(chat_id, text, reply_markup=main_menu(), parse_mode='HTML')
        last_bot_message[chat_id] = sent.message_id
        logger.info(f"Меню отправлено пользователю {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки меню пользователю {chat_id}: {e}")


def delete_message_safe(chat_id, message_id):
    """Безопасное удаление сообщения с обработкой ошибок"""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    logger.info(f"Пользователь {message.chat.id} запустил бота")
    send_menu(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Вернуться в меню")
def return_to_menu(message):
    """Обработчик кнопки 'Вернуться в меню'"""
    chat_id = message.chat.id
    logger.info(f"Пользователь {chat_id} вернулся в меню")

    # Очистка состояний пользователя
    user_states.pop(chat_id, None)
    user_data.pop(chat_id, None)

    # Удаление сообщений
    delete_message_safe(chat_id, message.message_id)
    if chat_id in last_bot_message:
        delete_message_safe(chat_id, last_bot_message[chat_id])
        del last_bot_message[chat_id]

    send_menu(chat_id, "<b>Ты вернулся в главное меню. 🔙</b>")


@bot.message_handler(func=lambda message: message.text == "📩 Обращение в Совет")
def handle_appeal(message):
    """Обработчик кнопки 'Обращение в Совет'"""
    chat_id = message.chat.id
    logger.info(f"Пользователь {chat_id} начал создание обращения")

    delete_message_safe(chat_id, message.message_id)
    if chat_id in last_bot_message:
        delete_message_safe(chat_id, last_bot_message[chat_id])
        del last_bot_message[chat_id]

    appeal_text = """<b>📩 Обращение в Совет</b>

💬 Ты выбрал раздел обращений — это отличный способ поделиться своими идеями, проблемами или предложениями! Мы всегда рады услышать твое мнение о правах детей, школьной жизни или молодежных проектах в Амурской области.

<b>Твой голос важен — пиши смело!</b> ✍️"""

    try:
        sent = bot.send_message(chat_id, appeal_text, reply_markup=back_to_menu(), parse_mode='HTML')
        last_bot_message[chat_id] = sent.message_id
        user_states[chat_id] = 'appeal'
    except Exception as e:
        logger.error(f"Ошибка при отправке запроса на обращение пользователю {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "📝 Заявка на вступление в Совет")
def handle_application(message):
    """Обработчик кнопки 'Заявка на вступление в Совет'"""
    chat_id = message.chat.id
    logger.info(f"Пользователь {chat_id} начал заполнение заявки")

    delete_message_safe(chat_id, message.message_id)
    if chat_id in last_bot_message:
        delete_message_safe(chat_id, last_bot_message[chat_id])
        del last_bot_message[chat_id]

    welcome_text = """<b>📋 Заявка на вступление в Совет</b>

🌟 Отлично! Ты решил присоединиться к нашей команде!

📍 <b>Важно:</b> Пока мы принимаем ребят только из города Благовещенска.

Чтобы подать заявку, нужно заполнить небольшую анкету. Это поможет нам лучше тебя узнать и понять, как ты можешь участвовать в работе Совета.

<b>Начнем! Укажи твое ФИО:</b> 📝"""

    try:
        sent = bot.send_message(chat_id, welcome_text, reply_markup=back_to_menu(), parse_mode='HTML')
        last_bot_message[chat_id] = sent.message_id
        user_states[chat_id] = 'application_fio'
        user_data[chat_id] = {}
    except Exception as e:
        logger.error(f"Ошибка при начале заявки для пользователя {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация о Совете")
def handle_info(message):
    """Обработчик кнопки 'Информация о Совете'"""
    chat_id = message.chat.id
    logger.info(f"Пользователь {chat_id} запросил информацию о Совете")

    delete_message_safe(chat_id, message.message_id)
    if chat_id in last_bot_message:
        delete_message_safe(chat_id, last_bot_message[chat_id])
        del last_bot_message[chat_id]

    try:
        sent = bot.send_message(chat_id, COUNCIL_INFO, reply_markup=back_to_menu(), parse_mode='HTML')
        last_bot_message[chat_id] = sent.message_id
    except Exception as e:
        logger.error(f"Ошибка при отправке информации о Совете пользователю {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "👥 Руководство Совета")
def handle_leadership(message):
    """Обработчик кнопки 'Руководство Совета'"""
    chat_id = message.chat.id
    logger.info(f"Пользователь {chat_id} запросил информацию о руководстве")

    delete_message_safe(chat_id, message.message_id)
    if chat_id in last_bot_message:
        delete_message_safe(chat_id, last_bot_message[chat_id])
        del last_bot_message[chat_id]

    try:
        sent = bot.send_message(chat_id, LEADERSHIP_INFO, reply_markup=back_to_menu(), parse_mode='HTML')
        last_bot_message[chat_id] = sent.message_id
    except Exception as e:
        logger.error(f"Ошибка при отправке информации о руководстве пользователю {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.chat.id not in [APPEAL_CHAT_ID, APPLICATION_CHAT_ID])
def handle_user_message(message):
    """Обработчик всех текстовых сообщений от пользователей"""
    chat_id = message.chat.id

    if chat_id not in user_states:
        # Пользователь отправил сообщение вне состояния
        logger.warning(f"Пользователь {chat_id} отправил сообщение вне состояния: {message.text}")
        return

    state = user_states[chat_id]
    logger.info(f"Обработка сообщения от пользователя {chat_id} в состоянии {state}")

    try:
        if state == 'appeal':
            # Пересылка обращения в чат администраторов
            forwarded = bot.forward_message(APPEAL_CHAT_ID, chat_id, message.message_id)
            responses_map[(APPEAL_CHAT_ID, forwarded.message_id)] = chat_id

            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, "Твое обращение было отправлено. ✅",
                                   reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            del user_states[chat_id]
            logger.info(f"Обращение от пользователя {chat_id} отправлено")

        elif state == 'application_fio':
            user_data[chat_id]['fio'] = message.text
            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, "<b>Укажи свой возраст:</b> 🎂\n\n<i>Например: 15</i>",
                                   reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_age'

        elif state == 'application_age':
            user_data[chat_id]['age'] = message.text
            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, '<b>Укажи школу обучения:</b> 🏫\n\n<i>Пример: МАОУ "Школа №26 г.Благовещенска"</i>',
                                   reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_school'

        elif state == 'application_school':
            user_data[chat_id]['school'] = message.text
            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, "<b>Укажи класс обучения:</b> 📚\n\n<i>Например: 9А или 11Б</i>",
                                   reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_class'

        elif state == 'application_class':
            user_data[chat_id]['class'] = message.text
            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, "<b>Укажи свой никнейм в Telegram:</b> 📱\n\n<i>Начинается с @, его можно найти в настройках профиля.</i> <b>Без него мы не сможем обработать твою заявку!</b>\n\n<i>Пример: @ivanov_ivan</i>",
                                   reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_username'

        elif state == 'application_username':
            user_data[chat_id]['username'] = message.text
            motivation_text = """<b>Расскажи, почему ты хочешь вступить в Совет:</b> 💭

<i>Опиши свою мотивацию, что тебя интересует в нашей работе, какие цели ты ставишь перед собой. Это поможет нам понять, насколько серьезны твои намерения.</i>

<i>Пример: "Хочу защищать права детей в нашем регионе, участвовать в разработке молодежных проектов и развивать свои лидерские качества"</i>"""

            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, motivation_text, reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_motivation'

        elif state == 'application_motivation':
            user_data[chat_id]['motivation'] = message.text
            experience_text = """<b>Расскажи о своем опыте общественной деятельности:</b> 🌟

<b>Участвовал ли ты в школьном самоуправлении, волонтерской деятельности, общественных организациях? Если опыта пока нет — это не проблема, просто напиши "Опыта пока нет, но готов учиться"</b>

<b>Пример: "Был старостой класса 2 года, участвовал в экологических акциях, помогаю в школьной библиотеке"</b>"""

            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, experience_text, reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_experience'

        elif state == 'application_experience':
            user_data[chat_id]['experience'] = message.text
            contacts_text = """<b>Укажи дополнительные контакты для связи:</b> 📞

<b>Номер телефона, email или другие способы связи.</b>

<b>Пример: "Телефон: +7-XXX-XXX-XX-XX (мама), email: ivanov@mail.ru"</b>"""

            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, contacts_text, reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            user_states[chat_id] = 'application_contacts'

        elif state == 'application_contacts':
            user_data[chat_id]['contacts'] = message.text

            # Формирование финальной заявки
            application_text = f"""📋 <b>НОВАЯ ЗАЯВКА НА ВСТУПЛЕНИЕ В СОВЕТ</b>

👤 <b>Личные данные:</b>
• ФИО: {user_data[chat_id]['fio']}
• Возраст: {user_data[chat_id]['age']} лет
• Telegram: {user_data[chat_id]['username']}

🏫 <b>Образование:</b>
• Школа: {user_data[chat_id]['school']}
• Класс: {user_data[chat_id]['class']}

💭 <b>Мотивация:</b>
{user_data[chat_id]['motivation']}

🌟 <b>Опыт общественной деятельности:</b>
{user_data[chat_id]['experience']}

📞 <b>Контакты для связи:</b>
{user_data[chat_id]['contacts']}

---
✅ Заявка готова к рассмотрению"""

            sent_app = bot.send_message(APPLICATION_CHAT_ID, application_text, parse_mode='HTML')
            responses_map[(APPLICATION_CHAT_ID, sent_app.message_id)] = chat_id

            success_text = """🎉 <b>Заявка успешно отправлена!</b>

✅ Твоя заявка получена и будет рассмотрена в течение <b>5 рабочих дней</b>.

📩 Результат рассмотрения придет в этот чат.

💪 Спасибо за желание присоединиться к нашей команде! Мы ценим активную молодежь, которая хочет изменить мир к лучшему."""

            if chat_id in last_bot_message:
                delete_message_safe(chat_id, last_bot_message[chat_id])
                del last_bot_message[chat_id]

            sent = bot.send_message(chat_id, success_text, reply_markup=back_to_menu(), parse_mode='HTML')
            last_bot_message[chat_id] = sent.message_id
            del user_states[chat_id]
            del user_data[chat_id]
            logger.info(f"Заявка от пользователя {chat_id} успешно отправлена")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения пользователя {chat_id} в состоянии {state}: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже или вернитесь в меню.",
                        reply_markup=back_to_menu())


@bot.message_handler(func=lambda message: message.chat.id in [APPEAL_CHAT_ID, APPLICATION_CHAT_ID] and message.reply_to_message is not None)
def handle_response(message):
    """Обработчик ответов администраторов в чатах Совета"""
    key = (message.chat.id, message.reply_to_message.message_id)

    if key in responses_map:
        user_chat_id = responses_map[key]
        formatted_response = f"<b>Пришёл ответ от Совета!:</b> 📩\n\n{message.text}\n\n"

        try:
            bot.send_message(user_chat_id, formatted_response, parse_mode='HTML')
            bot.reply_to(message, "✅ Ответ отправлен пользователю.")
            logger.info(f"Ответ от Совета отправлен пользователю {user_chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа пользователю {user_chat_id}: {e}")
            bot.reply_to(message, "❌ Ошибка при отправке ответа пользователю.")


if __name__ == '__main__':
    logger.info("Бот запущен")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка бота: {e}")

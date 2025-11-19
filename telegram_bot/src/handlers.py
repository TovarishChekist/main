# -*- coding: utf-8 -*-
"""
Модуль обработчиков сообщений (версия 2.0 с БД и медиафайлами)
Содержит всю логику обработки пользовательских команд и сообщений
"""

import logging
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from .config import config
from .messages import messages
from .keyboards import keyboards
from .states import state_manager, UserState
from .validators import validators
from .utils import MessageManager, response_mapper
from .database import Database

logger = logging.getLogger(__name__)


class BotHandlers:
    """Класс с обработчиками сообщений бота"""

    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.msg_manager = MessageManager()

    def register_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды
        self.bot.register_message_handler(self.cmd_start, commands=['start'])
        self.bot.register_message_handler(self.cmd_help, commands=['help'])
        self.bot.register_message_handler(self.cmd_my_applications, commands=['my_applications'])
        self.bot.register_message_handler(self.cmd_stats, commands=['stats'])

        # Админ-команды
        self.bot.register_message_handler(self.cmd_admin, commands=['admin'])
        self.bot.register_message_handler(self.cmd_block, commands=['block'])
        self.bot.register_message_handler(self.cmd_unblock, commands=['unblock'])
        self.bot.register_message_handler(self.cmd_blocked_list, commands=['blocked_list'])
        self.bot.register_message_handler(self.cmd_user_info, commands=['user_info'])
        self.bot.register_message_handler(self.cmd_clear_logs, commands=['clear_logs'])

        # Callback-кнопки для админов
        self.bot.register_callback_query_handler(
            self.handle_admin_callback,
            func=lambda call: call.data.startswith('admin_')
        )

        # Кнопки главного меню
        self.bot.register_message_handler(
            self.handle_back_to_menu,
            func=lambda m: m.text in ["🔙 Вернуться в меню", "Вернуться в меню", "❌ Отменить"]
        )
        self.bot.register_message_handler(
            self.handle_appeal_button,
            func=lambda m: m.text == "📩 Обращение в Совет"
        )
        self.bot.register_message_handler(
            self.handle_application_button,
            func=lambda m: m.text == "📝 Заявка на вступление в Совет"
        )
        self.bot.register_message_handler(
            self.handle_info_button,
            func=lambda m: m.text == "ℹ️ Информация о Совете"
        )
        self.bot.register_message_handler(
            self.handle_leadership_button,
            func=lambda m: m.text == "👥 Руководство Совета"
        )
        self.bot.register_message_handler(
            self.handle_faq_button,
            func=lambda m: m.text == "❓ FAQ"
        )

        # Ответы от администраторов в группах
        self.bot.register_message_handler(
            self.handle_admin_response,
            func=lambda m: m.chat.id in [config.APPEAL_CHAT_ID, config.APPLICATION_CHAT_ID]
                          and m.reply_to_message is not None
        )

        # Обработка медиафайлов (фото, документы, видео)
        self.bot.register_message_handler(
            self.handle_media,
            content_types=['photo', 'document', 'video'],
            func=lambda m: m.chat.id not in [config.APPEAL_CHAT_ID, config.APPLICATION_CHAT_ID]
        )

        # Обработка текстовых сообщений от пользователей
        self.bot.register_message_handler(
            self.handle_user_message,
            content_types=['text'],
            func=lambda m: m.chat.id not in [config.APPEAL_CHAT_ID, config.APPLICATION_CHAT_ID]
        )

        logger.info("Все обработчики зарегистрированы")

    # ============ Команды ============

    def cmd_start(self, message: Message):
        """Обработчик команды /start"""
        user = message.from_user
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")

        # Сохраняем пользователя в БД
        self.db.add_or_update_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )

        # Проверяем блокировку
        if self.db.is_user_blocked(user.id):
            block_info = self.db.get_block_info(user.id)
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.USER_IS_BLOCKED.format(reason=block_info['reason']),
                parse_mode='HTML'
            )
            return

        # Логируем событие
        self.db.log_event('bot_start', f'user_id:{user.id}')

        self._send_main_menu(message.chat.id)

    def cmd_help(self, message: Message):
        """Обработчик команды /help"""
        help_text = """<b>📖 Помощь по использованию бота</b>

<b>Доступные функции:</b>

📩 <b>Обращение в Совет</b> - отправить свое обращение, вопрос или предложение (можно с фото/документами)

📝 <b>Заявка на вступление</b> - подать заявку на вступление в Совет (только для Благовещенска)

ℹ️ <b>Информация о Совете</b> - узнать о целях и задачах Совета

👥 <b>Руководство Совета</b> - посмотреть состав руководства

❓ <b>FAQ</b> - ответы на частые вопросы

<b>Команды:</b>
/start - Вернуться в главное меню
/help - Показать эту справку
/my_applications - Мои заявки и обращения

<b>Нужна помощь?</b> Напиши нам через раздел "Обращение в Совет"!"""

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            help_text,
            parse_mode='HTML',
            reply_markup=keyboards.main_menu()
        )

    def cmd_my_applications(self, message: Message):
        """Показать мои заявки и обращения"""
        user_id = message.from_user.id

        # Получаем заявки
        applications = self.db.get_user_applications(user_id)
        # Получаем обращения
        appeals = self.db.get_user_appeals(user_id)

        text = "<b>📋 Мои заявки и обращения</b>\n\n"

        if applications:
            text += "<b>📝 Заявки на вступление:</b>\n"
            for app in applications:
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌'
                }.get(app['status'], '❓')

                status_text = {
                    'pending': 'На рассмотрении',
                    'approved': 'Одобрена',
                    'rejected': 'Отклонена'
                }.get(app['status'], app['status'])

                text += f"\n{status_emoji} <b>Заявка #{app['id']}</b>\n"
                text += f"Дата: {app['created_at'][:10]}\n"
                text += f"Статус: {status_text}\n"
                if app['review_comment']:
                    text += f"Комментарий: {app['review_comment']}\n"
        else:
            text += "📝 У вас пока нет заявок\n\n"

        if appeals:
            text += "\n<b>📩 Обращения:</b>\n"
            for appeal in appeals:
                status_emoji = {
                    'new': '🆕',
                    'answered': '✅',
                    'closed': '🔒'
                }.get(appeal['status'], '❓')

                text += f"\n{status_emoji} <b>Обращение #{appeal['id']}</b>\n"
                text += f"Дата: {appeal['created_at'][:10]}\n"
                text += f"Текст: {appeal['text'][:50]}...\n"
                if appeal['response_text']:
                    text += f"📩 Ответ получен: {appeal['responded_at'][:10]}\n"
        else:
            text += "📩 У вас пока нет обращений\n"

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            text,
            parse_mode='HTML',
            reply_markup=keyboards.main_menu()
        )

    def cmd_stats(self, message: Message):
        """Статистика (только для админов)"""
        # Проверяем, является ли пользователь админом
        if message.chat.id not in [config.APPEAL_CHAT_ID, config.APPLICATION_CHAT_ID]:
            # Можно добавить список админов
            return

        stats = self.db.get_stats_summary()

        text = f"""<b>📊 Статистика бота</b>

👥 Всего пользователей: {stats['total_users']}

📩 Обращения:
• Всего: {stats['total_appeals']}
• Новых: {stats['new_appeals']}

📝 Заявки:
• Всего: {stats['total_applications']}
• На рассмотрении: {stats['pending_applications']}
• Одобрено: {stats['approved_applications']}
"""

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            text,
            parse_mode='HTML'
        )

    # ============ Админ-команды ============

    def _is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id == config.ADMIN_CHAT_ID

    def cmd_admin(self, message: Message):
        """Показать админ-панель"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            messages.ADMIN_PANEL,
            parse_mode='HTML'
        )

    def cmd_block(self, message: Message):
        """Заблокировать пользователя"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        # Парсинг команды: /block <user_id> <причина>
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/block <user_id> <причина>"),
                parse_mode='HTML'
            )
            return

        try:
            user_id = int(parts[1])
            reason = parts[2]
        except ValueError:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/block <user_id> <причина>"),
                parse_mode='HTML'
            )
            return

        # Нельзя заблокировать админа
        if user_id == config.ADMIN_CHAT_ID:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_CANNOT_BLOCK_ADMIN,
                parse_mode='HTML'
            )
            return

        # Проверяем, не заблокирован ли уже
        if self.db.is_user_blocked(user_id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_USER_ALREADY_BLOCKED,
                parse_mode='HTML'
            )
            return

        # Блокируем пользователя
        try:
            from datetime import datetime
            self.db.block_user(user_id, reason, message.from_user.id)
            blocked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Уведомляем админа
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.USER_BLOCKED.format(
                    user_id=user_id,
                    reason=reason,
                    blocked_at=blocked_at
                ),
                parse_mode='HTML'
            )

            # Уведомляем пользователя
            try:
                self.msg_manager.safe_send_message(
                    self.bot,
                    user_id,
                    messages.USER_IS_BLOCKED.format(reason=reason),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка при блокировке пользователя: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                f"❌ Ошибка при блокировке: {e}",
                parse_mode='HTML'
            )

    def cmd_unblock(self, message: Message):
        """Разблокировать пользователя"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        # Парсинг команды: /unblock <user_id>
        parts = message.text.split()
        if len(parts) != 2:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/unblock <user_id>"),
                parse_mode='HTML'
            )
            return

        try:
            user_id = int(parts[1])
        except ValueError:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/unblock <user_id>"),
                parse_mode='HTML'
            )
            return

        # Проверяем, заблокирован ли пользователь
        if not self.db.is_user_blocked(user_id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_USER_NOT_BLOCKED,
                parse_mode='HTML'
            )
            return

        # Разблокируем
        try:
            from datetime import datetime
            self.db.unblock_user(user_id)
            unblocked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Уведомляем админа
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.USER_UNBLOCKED.format(
                    user_id=user_id,
                    unblocked_at=unblocked_at
                ),
                parse_mode='HTML'
            )

            # Уведомляем пользователя
            try:
                self.msg_manager.safe_send_message(
                    self.bot,
                    user_id,
                    messages.USER_WAS_UNBLOCKED,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка при разблокировке пользователя: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                f"❌ Ошибка при разблокировке: {e}",
                parse_mode='HTML'
            )

    def cmd_blocked_list(self, message: Message):
        """Список заблокированных пользователей"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        blocked_users = self.db.get_blocked_users()

        if not blocked_users:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.NO_BLOCKED_USERS,
                parse_mode='HTML'
            )
            return

        text = messages.BLOCKED_LIST_HEADER.format(count=len(blocked_users))

        for i, user in enumerate(blocked_users, 1):
            name = user.get('first_name', 'Неизвестно')
            if user.get('last_name'):
                name += f" {user['last_name']}"

            username = f"@{user['username']}" if user.get('username') else 'нет username'

            text += messages.BLOCKED_USER_ITEM.format(
                num=i,
                user_id=user['user_id'],
                name=name,
                username=username,
                reason=user['reason'],
                blocked_at=user['blocked_at'][:16]
            )

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            text,
            parse_mode='HTML'
        )

    def cmd_user_info(self, message: Message):
        """Информация о пользователе"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        # Парсинг команды: /user_info <user_id>
        parts = message.text.split()
        if len(parts) != 2:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/user_info <user_id>"),
                parse_mode='HTML'
            )
            return

        try:
            user_id = int(parts[1])
        except ValueError:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_INVALID_COMMAND.format(usage="/user_info <user_id>"),
                parse_mode='HTML'
            )
            return

        # Получаем информацию о пользователе
        user = self.db.get_user(user_id)
        if not user:
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_USER_NOT_FOUND,
                parse_mode='HTML'
            )
            return

        # Формируем информацию
        text = f"""👤 <b>Информация о пользователе</b>

<b>ID:</b> {user['user_id']}
<b>Имя:</b> {user.get('first_name', 'Неизвестно')}
<b>Фамилия:</b> {user.get('last_name', 'Нет')}
<b>Username:</b> @{user.get('username', 'нет')}
<b>Дата регистрации:</b> {user['created_at'][:16]}
<b>Последняя активность:</b> {user['last_active'][:16]}

"""

        # Проверяем блокировку
        if self.db.is_user_blocked(user_id):
            block_info = self.db.get_block_info(user_id)
            text += f"""<b>🚫 Статус:</b> Заблокирован
<b>Причина:</b> {block_info['reason']}
<b>Дата блокировки:</b> {block_info['blocked_at'][:16]}
"""
        else:
            text += "<b>✅ Статус:</b> Активен\n"

        # Статистика пользователя
        appeals = self.db.get_user_appeals(user_id)
        applications = self.db.get_user_applications(user_id)

        text += f"""
<b>📊 Статистика:</b>
• Обращений: {len(appeals)}
• Заявок: {len(applications)}
"""

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            text,
            parse_mode='HTML'
        )

    def cmd_clear_logs(self, message: Message):
        """Очистить файл логов"""
        if not self._is_admin(message.from_user.id):
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.ERROR_NOT_ADMIN,
                parse_mode='HTML'
            )
            return

        try:
            # Очищаем файл логов
            with open(config.LOG_FILE, 'w', encoding='utf-8') as f:
                f.write('')

            logger.info(f"Логи очищены администратором {message.from_user.id}")

            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                messages.LOGS_CLEARED,
                parse_mode='HTML'
            )

        except Exception as e:
            logger.error(f"Ошибка при очистке логов: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                message.chat.id,
                f"❌ Ошибка при очистке логов: {e}",
                parse_mode='HTML'
            )

    # ============ Главное меню ============

    def _send_main_menu(self, chat_id: int, text: str = None):
        """Отправка главного меню"""
        if text is None:
            text = messages.WELCOME

        # Обновленное меню с кнопкой FAQ
        from telebot.types import ReplyKeyboardMarkup, KeyboardButton
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(KeyboardButton("📩 Обращение в Совет"))
        markup.add(KeyboardButton("📝 Заявка на вступление в Совет"))
        markup.add(KeyboardButton("ℹ️ Информация о Совете"))
        markup.add(KeyboardButton("👥 Руководство Совета"))
        markup.add(KeyboardButton("❓ FAQ"))

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            text,
            parse_mode='HTML',
            reply_markup=markup
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.IDLE)

    def handle_back_to_menu(self, message: Message):
        """Обработчик кнопки возврата в меню"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} возвращается в главное меню")

        # Сбрасываем состояние
        state_manager.reset_state(chat_id)

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем последнее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем меню
        self._send_main_menu(chat_id, messages.BACK_TO_MENU)

    # ============ Обработчики кнопок меню ============

    def handle_appeal_button(self, message: Message):
        """Обработчик кнопки 'Обращение в Совет'"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} начал создание обращения")

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем промпт с упоминанием о медиафайлах
        appeal_text = messages.APPEAL_PROMPT + "\n\n<i>Вы можете прикрепить фото или документ к вашему обращению.</i>"
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            appeal_text,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPEAL)

    def handle_faq_button(self, message: Message):
        """Обработчик кнопки FAQ"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} открыл FAQ")

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        faq_text = """<b>❓ Часто задаваемые вопросы</b>

<b>1. Кто может вступить в Совет?</b>
В Совет могут вступить дети и молодёжь от 10 до 25 лет, проживающие в Благовещенске.

<b>2. Сколько рассматривается заявка?</b>
Заявки рассматриваются в течение 5 рабочих дней. Результат придет в этот чат.

<b>3. Какие документы нужны для вступления?</b>
Специальные документы не требуются, достаточно заполнить заявку в боте.

<b>4. Чем занимается Совет?</b>
Мы защищаем права детей, организуем мероприятия, проводим акции и помогаем развивать молодежные инициативы.

<b>5. Как связаться с Советом?</b>
Используйте раздел "Обращение в Совет" в этом боте, и мы ответим вам в ближайшее время.

<b>6. Могу ли я отправить фото в обращении?</b>
Да! Просто прикрепите фото или документ к сообщению.

<b>7. Как узнать статус моей заявки?</b>
Используйте команду /my_applications

<b>Остались вопросы?</b> Задайте их через раздел "Обращение в Совет"!"""

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            faq_text,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

    def handle_application_button(self, message: Message):
        """Обработчик кнопки 'Заявка на вступление в Совет'"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} начал заполнение заявки")

        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_WELCOME,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_FIO)

    def handle_info_button(self, message: Message):
        """Обработчик кнопки 'Информация о Совете'"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} запросил информацию о Совете")

        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.COUNCIL_INFO,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

    def handle_leadership_button(self, message: Message):
        """Обработчик кнопки 'Руководство Совета'"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} запросил информацию о руководстве")

        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.LEADERSHIP_INFO,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

    # ============ Обработка медиафайлов ============

    def handle_media(self, message: Message):
        """Обработка фото, документов, видео"""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Проверяем блокировку
        if not self._is_admin(user_id):
            if self.db.is_user_blocked(user_id):
                block_info = self.db.get_block_info(user_id)
                self.msg_manager.safe_send_message(
                    self.bot,
                    chat_id,
                    messages.USER_IS_BLOCKED.format(reason=block_info['reason']),
                    parse_mode='HTML'
                )
                return

        current_state = state_manager.get_state(chat_id)

        # Медиафайлы поддерживаются только для обращений
        if current_state == UserState.APPEAL:
            self._process_appeal_with_media(message)
        else:
            # В других случаях предлагаем вернуться в меню
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                "Медиафайлы можно отправлять только в разделе 'Обращение в Совет'",
                reply_markup=keyboards.main_menu()
            )

    def _process_appeal_with_media(self, message: Message):
        """Обработка обращения с медиафайлом"""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Определяем тип медиа и file_id
        media_type = None
        media_file_id = None
        caption = message.caption or "Обращение с медиафайлом"

        if message.photo:
            media_type = 'photo'
            media_file_id = message.photo[-1].file_id  # Берем самое большое фото
        elif message.document:
            media_type = 'document'
            media_file_id = message.document.file_id
        elif message.video:
            media_type = 'video'
            media_file_id = message.video.file_id

        logger.info(f"Получено обращение с {media_type} от пользователя {user_id}")

        # Сохраняем в БД
        try:
            appeal_id = self.db.add_appeal(user_id, caption, media_type, media_file_id)
            self.db.log_event('appeal_created', f'user:{user_id},appeal:{appeal_id},media:{media_type}')

            # Пересылаем в группу
            if media_type == 'photo':
                forwarded = self.bot.send_photo(
                    config.APPEAL_CHAT_ID,
                    media_file_id,
                    caption=f"📩 <b>Обращение #{appeal_id}</b>\n\n{caption}\n\n👤 От: {message.from_user.first_name}",
                    parse_mode='HTML'
                )
            elif media_type == 'document':
                forwarded = self.bot.send_document(
                    config.APPEAL_CHAT_ID,
                    media_file_id,
                    caption=f"📩 <b>Обращение #{appeal_id}</b>\n\n{caption}\n\n👤 От: {message.from_user.first_name}",
                    parse_mode='HTML'
                )
            elif media_type == 'video':
                forwarded = self.bot.send_video(
                    config.APPEAL_CHAT_ID,
                    media_file_id,
                    caption=f"📩 <b>Обращение #{appeal_id}</b>\n\n{caption}\n\n👤 От: {message.from_user.first_name}",
                    parse_mode='HTML'
                )

            response_mapper.add(config.APPEAL_CHAT_ID, forwarded.message_id, chat_id)

            # Добавляем админ-кнопки к сообщению
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Отметить обработанным", callback_data=f"admin_appeal_done_{appeal_id}")
            )
            self.bot.edit_message_reply_markup(
                config.APPEAL_CHAT_ID,
                forwarded.message_id,
                reply_markup=markup
            )

        except Exception as e:
            logger.error(f"Ошибка при обработке обращения с медиа: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                "❌ Произошла ошибка при отправке обращения. Попробуйте позже.",
                parse_mode='HTML'
            )
            return

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем подтверждение
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPEAL_SUCCESS,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

        state_manager.set_state(chat_id, UserState.IDLE)

    # ============ Обработка текстовых сообщений ============

    def handle_user_message(self, message: Message):
        """Обработчик текстовых сообщений от пользователей"""
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Проверяем блокировку (кроме админа и групповых чатов)
        if chat_id > 0 and not self._is_admin(user_id):  # Приватный чат
            if self.db.is_user_blocked(user_id):
                block_info = self.db.get_block_info(user_id)
                self.msg_manager.safe_send_message(
                    self.bot,
                    chat_id,
                    messages.USER_IS_BLOCKED.format(reason=block_info['reason']),
                    parse_mode='HTML'
                )
                return

        current_state = state_manager.get_state(chat_id)

        # Обработка в зависимости от состояния
        if current_state == UserState.APPEAL:
            self._process_appeal(message)
        elif current_state == UserState.APPLICATION_FIO:
            self._process_application_fio(message)
        elif current_state == UserState.APPLICATION_AGE:
            self._process_application_age(message)
        elif current_state == UserState.APPLICATION_SCHOOL:
            self._process_application_school(message)
        elif current_state == UserState.APPLICATION_CLASS:
            self._process_application_class(message)
        elif current_state == UserState.APPLICATION_USERNAME:
            self._process_application_username(message)
        elif current_state == UserState.APPLICATION_MOTIVATION:
            self._process_application_motivation(message)
        elif current_state == UserState.APPLICATION_EXPERIENCE:
            self._process_application_experience(message)
        elif current_state == UserState.APPLICATION_CONTACTS:
            self._process_application_contacts(message)
        else:
            # Если нет активного состояния, показываем меню
            self._send_main_menu(chat_id)

    # ============ Обработка обращений ============

    def _process_appeal(self, message: Message):
        """Обработка текстового обращения"""
        chat_id = message.chat.id
        user_id = message.from_user.id
        logger.info(f"Обработка обращения от пользователя {user_id}")

        # Валидация
        is_valid, error = validators.validate_text_length(message.text, min_length=10, max_length=2000)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем в БД
        try:
            appeal_id = self.db.add_appeal(user_id, message.text)
            self.db.log_event('appeal_created', f'user:{user_id},appeal:{appeal_id}')

            # Пересылаем в группу с админ-кнопками
            appeal_text = f"""📩 <b>Обращение #{appeal_id}</b>

{message.text}

👤 <b>От:</b> {message.from_user.first_name} (@{message.from_user.username or 'нет username'})"""

            forwarded = self.bot.send_message(
                config.APPEAL_CHAT_ID,
                appeal_text,
                parse_mode='HTML'
            )

            # Добавляем админ-кнопки
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Отметить обработанным", callback_data=f"admin_appeal_done_{appeal_id}")
            )
            self.bot.edit_message_reply_markup(
                config.APPEAL_CHAT_ID,
                forwarded.message_id,
                reply_markup=markup
            )

            response_mapper.add(config.APPEAL_CHAT_ID, forwarded.message_id, chat_id)
            logger.info(f"Обращение #{appeal_id} переслано в группу {config.APPEAL_CHAT_ID}")

        except Exception as e:
            logger.error(f"Ошибка при пересылке обращения: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                "❌ Произошла ошибка при отправке обращения. Попробуйте позже.",
                parse_mode='HTML'
            )
            return

        # Удаляем предыдущее сообщение бота
        self._delete_last_bot_message(chat_id)

        # Отправляем подтверждение
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPEAL_SUCCESS,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

        state_manager.set_state(chat_id, UserState.IDLE)

    # ========== Обработка заявки (методы остаются теми же) ==========

    def _process_application_fio(self, message: Message):
        """Обработка ФИО"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_fio(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'fio', message.text)
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_AGE, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_AGE)

    def _process_application_age(self, message: Message):
        """Обработка возраста"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_age(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'age', message.text.strip())
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_SCHOOL, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_SCHOOL)

    def _process_application_school(self, message: Message):
        """Обработка школы"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_school(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'school', message.text)
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_CLASS, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_CLASS)

    def _process_application_class(self, message: Message):
        """Обработка класса"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_class(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'class', message.text.strip())
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_USERNAME, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_USERNAME)

    def _process_application_username(self, message: Message):
        """Обработка никнейма"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_username(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'username', message.text.strip())
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_MOTIVATION, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_MOTIVATION)

    def _process_application_motivation(self, message: Message):
        """Обработка мотивации"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_text_length(message.text, min_length=20, max_length=1000)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'motivation', message.text)
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_EXPERIENCE, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_EXPERIENCE)

    def _process_application_experience(self, message: Message):
        """Обработка опыта"""
        chat_id = message.chat.id
        is_valid, error = validators.validate_text_length(message.text, min_length=10, max_length=1000)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'experience', message.text)
        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_CONTACTS, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_CONTACTS)

    def _process_application_contacts(self, message: Message):
        """Обработка контактов и отправка заявки"""
        chat_id = message.chat.id
        user_id = message.from_user.id
        is_valid, error = validators.validate_contacts(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(self.bot, chat_id, f"❌ <b>{error}</b>\n\nПопробуй еще раз:", parse_mode='HTML', reply_markup=keyboards.back_to_menu())
            return
        state_manager.set_data(chat_id, 'contacts', message.text)
        application_data = state_manager.get_all_data(chat_id)

        # Сохраняем заявку в БД
        try:
            app_id = self.db.add_application(user_id, application_data)
            self.db.log_event('application_created', f'user:{user_id},app:{app_id}')

            application_text = messages.format_application(application_data)
            application_text = application_text.replace("📋 <b>НОВАЯ ЗАЯВКА НА ВСТУПЛЕНИЕ В СОВЕТ</b>", f"📋 <b>ЗАЯВКА #{app_id} НА ВСТУПЛЕНИЕ В СОВЕТ</b>")

            sent_app = self.bot.send_message(config.APPLICATION_CHAT_ID, application_text, parse_mode='HTML')

            # Добавляем админ-кнопки
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_app_approve_{app_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_app_reject_{app_id}")
            )
            self.bot.edit_message_reply_markup(config.APPLICATION_CHAT_ID, sent_app.message_id, reply_markup=markup)
            response_mapper.add(config.APPLICATION_CHAT_ID, sent_app.message_id, chat_id)
            logger.info(f"Заявка #{app_id} от пользователя {user_id} отправлена в группу")
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")
            self.msg_manager.safe_send_message(self.bot, chat_id, "❌ Произошла ошибка при отправке заявки. Попробуйте позже.", parse_mode='HTML')
            return

        self._delete_last_bot_message(chat_id)
        sent = self.msg_manager.safe_send_message(self.bot, chat_id, messages.APPLICATION_SUCCESS, parse_mode='HTML', reply_markup=keyboards.back_to_menu())
        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
        state_manager.reset_state(chat_id)

    # ============ Админ-панель с кнопками ============

    def handle_admin_callback(self, call):
        """Обработчик callback-кнопок для админов"""
        data = call.data

        # Обработка заявок
        if data.startswith('admin_app_approve_'):
            app_id = int(data.split('_')[-1])
            self.db.update_application_status(app_id, 'approved', 'Заявка одобрена')
            self.db.log_event('application_approved', f'app:{app_id}')

            # Уведомляем пользователя
            user_chat_id = response_mapper.get(call.message.chat.id, call.message.message_id)
            if user_chat_id:
                self.bot.send_message(user_chat_id, "🎉 <b>Поздравляем!</b>\n\nВаша заявка на вступление в Совет одобрена! Скоро с вами свяжутся.", parse_mode='HTML')

            # Обновляем сообщение в группе
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            self.bot.answer_callback_query(call.id, "✅ Заявка одобрена")

        elif data.startswith('admin_app_reject_'):
            app_id = int(data.split('_')[-1])
            self.db.update_application_status(app_id, 'rejected', 'Заявка отклонена')
            self.db.log_event('application_rejected', f'app:{app_id}')

            # Уведомляем пользователя
            user_chat_id = response_mapper.get(call.message.chat.id, call.message.message_id)
            if user_chat_id:
                self.bot.send_message(user_chat_id, "К сожалению, ваша заявка на вступление в Совет отклонена. Вы можете подать новую заявку позже.", parse_mode='HTML')

            # Обновляем сообщение в группе
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            self.bot.answer_callback_query(call.id, "❌ Заявка отклонена")

        elif data.startswith('admin_appeal_done_'):
            appeal_id = int(data.split('_')[-1])
            self.db.update_appeal_status(appeal_id, 'answered')
            self.db.log_event('appeal_answered', f'appeal:{appeal_id}')

            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            self.bot.answer_callback_query(call.id, "✅ Обращение отмечено обработанным")

    # ============ Обработка ответов от администраторов ============

    def handle_admin_response(self, message: Message):
        """Обработчик ответов администраторов в группах"""
        if not message.reply_to_message:
            return

        chat_id = message.chat.id
        replied_msg_id = message.reply_to_message.message_id

        # Получаем ID пользователя из мапы
        user_chat_id = response_mapper.get(chat_id, replied_msg_id)

        if user_chat_id:
            # Формируем и отправляем ответ пользователю
            response_text = messages.RESPONSE_FROM_COUNCIL.format(text=message.text)

            sent = self.msg_manager.safe_send_message(
                self.bot,
                user_chat_id,
                response_text,
                parse_mode='HTML'
            )

            if sent:
                # Подтверждаем отправку
                self.bot.reply_to(message, messages.RESPONSE_SENT)
                logger.info(f"Ответ от группы {chat_id} отправлен пользователю {user_chat_id}")
        else:
            logger.warning(f"Не найден пользователь для ответа в группе {chat_id}, сообщение {replied_msg_id}")

    # ============ Вспомогательные методы ============

    def _delete_last_bot_message(self, chat_id: int):
        """Удаление последнего сообщения бота"""
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

# -*- coding: utf-8 -*-
"""
Модуль обработчиков сообщений
Содержит всю логику обработки пользовательских команд и сообщений
"""

import logging
from telebot import TeleBot
from telebot.types import Message

from .config import config
from .messages import messages
from .keyboards import keyboards
from .states import state_manager, UserState
from .validators import validators
from .utils import MessageManager, response_mapper

logger = logging.getLogger(__name__)


class BotHandlers:
    """Класс с обработчиками сообщений бота"""

    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.msg_manager = MessageManager()

    def register_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды
        self.bot.register_message_handler(self.cmd_start, commands=['start'])
        self.bot.register_message_handler(self.cmd_help, commands=['help'])

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

        # Ответы от администраторов в группах
        self.bot.register_message_handler(
            self.handle_admin_response,
            func=lambda m: m.chat.id in [config.APPEAL_CHAT_ID, config.APPLICATION_CHAT_ID]
                          and m.reply_to_message is not None
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
        logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) запустил бота")
        self._send_main_menu(message.chat.id)

    def cmd_help(self, message: Message):
        """Обработчик команды /help"""
        help_text = """<b>📖 Помощь по использованию бота</b>

<b>Доступные функции:</b>

📩 <b>Обращение в Совет</b> - отправить свое обращение, вопрос или предложение

📝 <b>Заявка на вступление</b> - подать заявку на вступление в Совет (только для Благовещенска)

ℹ️ <b>Информация о Совете</b> - узнать о целях и задачах Совета

👥 <b>Руководство Совета</b> - посмотреть состав руководства

<b>Команды:</b>
/start - Вернуться в главное меню
/help - Показать эту справку

<b>Нужна помощь?</b> Напиши нам через раздел "Обращение в Совет"!"""

        self.msg_manager.safe_send_message(
            self.bot,
            message.chat.id,
            help_text,
            parse_mode='HTML',
            reply_markup=keyboards.main_menu()
        )

    # ============ Главное меню ============

    def _send_main_menu(self, chat_id: int, text: str = None):
        """Отправка главного меню"""
        if text is None:
            text = messages.WELCOME

        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            text,
            parse_mode='HTML',
            reply_markup=keyboards.main_menu()
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

        # Отправляем промпт
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPEAL_PROMPT,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPEAL)

    def handle_application_button(self, message: Message):
        """Обработчик кнопки 'Заявка на вступление в Совет'"""
        chat_id = message.chat.id
        logger.info(f"Пользователь {message.from_user.id} начал заполнение заявки")

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем приветствие и запрос ФИО
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

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем информацию
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

        # Удаляем сообщение пользователя
        self.msg_manager.safe_delete_message(self.bot, chat_id, message.message_id)

        # Удаляем предыдущее сообщение бота
        last_msg_id = state_manager.get_last_message(chat_id)
        if last_msg_id:
            self.msg_manager.safe_delete_message(self.bot, chat_id, last_msg_id)

        # Отправляем информацию
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.LEADERSHIP_INFO,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

    # ============ Обработка пользовательских сообщений ============

    def handle_user_message(self, message: Message):
        """Обработчик текстовых сообщений от пользователей"""
        chat_id = message.chat.id
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
        """Обработка обращения"""
        chat_id = message.chat.id
        logger.info(f"Обработка обращения от пользователя {message.from_user.id}")

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

        # Пересылаем обращение в группу
        try:
            forwarded = self.bot.forward_message(config.APPEAL_CHAT_ID, chat_id, message.message_id)
            response_mapper.add(config.APPEAL_CHAT_ID, forwarded.message_id, chat_id)
            logger.info(f"Обращение переслано в группу {config.APPEAL_CHAT_ID}")
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

    # ============ Обработка заявки на вступление ============

    def _process_application_fio(self, message: Message):
        """Обработка ФИО"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_fio(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'fio', message.text)

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем возраст
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_AGE,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_AGE)

    def _process_application_age(self, message: Message):
        """Обработка возраста"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_age(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'age', message.text.strip())

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем школу
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_SCHOOL,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_SCHOOL)

    def _process_application_school(self, message: Message):
        """Обработка школы"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_school(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'school', message.text)

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем класс
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_CLASS,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_CLASS)

    def _process_application_class(self, message: Message):
        """Обработка класса"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_class(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'class', message.text.strip())

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем никнейм
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_USERNAME,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_USERNAME)

    def _process_application_username(self, message: Message):
        """Обработка никнейма"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_username(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'username', message.text.strip())

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем мотивацию
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_MOTIVATION,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_MOTIVATION)

    def _process_application_motivation(self, message: Message):
        """Обработка мотивации"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_text_length(message.text, min_length=20, max_length=1000)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'motivation', message.text)

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем опыт
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_EXPERIENCE,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_EXPERIENCE)

    def _process_application_experience(self, message: Message):
        """Обработка опыта"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_text_length(message.text, min_length=10, max_length=1000)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'experience', message.text)

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Запрашиваем контакты
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_CONTACTS,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)
            state_manager.set_state(chat_id, UserState.APPLICATION_CONTACTS)

    def _process_application_contacts(self, message: Message):
        """Обработка контактов и отправка заявки"""
        chat_id = message.chat.id

        # Валидация
        is_valid, error = validators.validate_contacts(message.text)
        if not is_valid:
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                f"❌ <b>{error}</b>\n\nПопробуй еще раз:",
                parse_mode='HTML',
                reply_markup=keyboards.back_to_menu()
            )
            return

        # Сохраняем данные
        state_manager.set_data(chat_id, 'contacts', message.text)

        # Получаем все данные
        application_data = state_manager.get_all_data(chat_id)

        # Формируем сообщение для группы
        application_text = messages.format_application(application_data)

        # Отправляем в группу
        try:
            sent_app = self.bot.send_message(config.APPLICATION_CHAT_ID, application_text, parse_mode='HTML')
            response_mapper.add(config.APPLICATION_CHAT_ID, sent_app.message_id, chat_id)
            logger.info(f"Заявка от пользователя {message.from_user.id} отправлена в группу")
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")
            self.msg_manager.safe_send_message(
                self.bot,
                chat_id,
                "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
                parse_mode='HTML'
            )
            return

        # Удаляем предыдущее сообщение
        self._delete_last_bot_message(chat_id)

        # Отправляем подтверждение
        sent = self.msg_manager.safe_send_message(
            self.bot,
            chat_id,
            messages.APPLICATION_SUCCESS,
            parse_mode='HTML',
            reply_markup=keyboards.back_to_menu()
        )

        if sent:
            state_manager.set_last_message(chat_id, sent.message_id)

        # Сбрасываем состояние
        state_manager.reset_state(chat_id)

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

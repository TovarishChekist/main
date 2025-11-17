# -*- coding: utf-8 -*-
"""
Вспомогательные утилиты
Общие функции для работы бота
"""

import logging
from typing import Optional
from telebot import TeleBot
from telebot.types import Message

logger = logging.getLogger(__name__)


class MessageManager:
    """Менеджер для работы с сообщениями"""

    @staticmethod
    def safe_delete_message(bot: TeleBot, chat_id: int, message_id: int) -> bool:
        """
        Безопасное удаление сообщения
        :param bot: Экземпляр бота
        :param chat_id: ID чата
        :param message_id: ID сообщения
        :return: True если удалено успешно
        """
        try:
            bot.delete_message(chat_id, message_id)
            return True
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")
            return False

    @staticmethod
    def safe_send_message(bot: TeleBot, chat_id: int, text: str, **kwargs) -> Optional[Message]:
        """
        Безопасная отправка сообщения
        :param bot: Экземпляр бота
        :param chat_id: ID чата
        :param text: Текст сообщения
        :param kwargs: Дополнительные параметры
        :return: Отправленное сообщение или None
        """
        try:
            return bot.send_message(chat_id, text, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")
            return None

    @staticmethod
    def safe_edit_message(bot: TeleBot, chat_id: int, message_id: int, text: str, **kwargs) -> bool:
        """
        Безопасное редактирование сообщения
        :param bot: Экземпляр бота
        :param chat_id: ID чата
        :param message_id: ID сообщения
        :param text: Новый текст
        :param kwargs: Дополнительные параметры
        :return: True если отредактировано успешно
        """
        try:
            bot.edit_message_text(text, chat_id, message_id, **kwargs)
            return True
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение {message_id} в чате {chat_id}: {e}")
            return False


class ResponseMapper:
    """Класс для управления мапой ответов (связь сообщений в группе с пользователями)"""

    def __init__(self):
        self._map: dict = {}  # (chat_id, message_id) -> user_chat_id

    def add(self, group_chat_id: int, group_message_id: int, user_chat_id: int) -> None:
        """Добавить связь между сообщением в группе и пользователем"""
        key = (group_chat_id, group_message_id)
        self._map[key] = user_chat_id
        logger.debug(f"Добавлена связь: группа {group_chat_id}, сообщение {group_message_id} -> пользователь {user_chat_id}")

    def get(self, group_chat_id: int, group_message_id: int) -> Optional[int]:
        """Получить ID пользователя по сообщению в группе"""
        key = (group_chat_id, group_message_id)
        return self._map.get(key)

    def remove(self, group_chat_id: int, group_message_id: int) -> None:
        """Удалить связь"""
        key = (group_chat_id, group_message_id)
        if key in self._map:
            del self._map[key]


# Создаем глобальный экземпляр мапера ответов
response_mapper = ResponseMapper()

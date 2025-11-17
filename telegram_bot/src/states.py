# -*- coding: utf-8 -*-
"""
Модуль с состояниями бота
Управление состояниями пользователей
"""

from enum import Enum
from typing import Dict, Optional, Any


class UserState(Enum):
    """Перечисление возможных состояний пользователя"""
    IDLE = "idle"  # Ожидание действия
    APPEAL = "appeal"  # Ввод обращения
    APPLICATION_FIO = "application_fio"
    APPLICATION_AGE = "application_age"
    APPLICATION_SCHOOL = "application_school"
    APPLICATION_CLASS = "application_class"
    APPLICATION_USERNAME = "application_username"
    APPLICATION_MOTIVATION = "application_motivation"
    APPLICATION_EXPERIENCE = "application_experience"
    APPLICATION_CONTACTS = "application_contacts"


class StateManager:
    """Менеджер состояний пользователей"""

    def __init__(self):
        self._states: Dict[int, UserState] = {}
        self._data: Dict[int, Dict[str, Any]] = {}
        self._last_messages: Dict[int, int] = {}

    def set_state(self, chat_id: int, state: UserState) -> None:
        """Установить состояние пользователя"""
        self._states[chat_id] = state

    def get_state(self, chat_id: int) -> Optional[UserState]:
        """Получить текущее состояние пользователя"""
        return self._states.get(chat_id, UserState.IDLE)

    def reset_state(self, chat_id: int) -> None:
        """Сбросить состояние пользователя"""
        if chat_id in self._states:
            del self._states[chat_id]
        if chat_id in self._data:
            del self._data[chat_id]
        if chat_id in self._last_messages:
            del self._last_messages[chat_id]

    def set_data(self, chat_id: int, key: str, value: Any) -> None:
        """Сохранить данные пользователя"""
        if chat_id not in self._data:
            self._data[chat_id] = {}
        self._data[chat_id][key] = value

    def get_data(self, chat_id: int, key: str = None) -> Optional[Any]:
        """Получить данные пользователя"""
        if key:
            return self._data.get(chat_id, {}).get(key)
        return self._data.get(chat_id, {})

    def get_all_data(self, chat_id: int) -> Dict[str, Any]:
        """Получить все данные пользователя"""
        return self._data.get(chat_id, {})

    def set_last_message(self, chat_id: int, message_id: int) -> None:
        """Сохранить ID последнего сообщения бота"""
        self._last_messages[chat_id] = message_id

    def get_last_message(self, chat_id: int) -> Optional[int]:
        """Получить ID последнего сообщения бота"""
        return self._last_messages.get(chat_id)


# Создаем глобальный экземпляр менеджера состояний
state_manager = StateManager()

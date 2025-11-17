# -*- coding: utf-8 -*-
"""
Модуль с клавиатурами бота
Содержит все клавиатуры для взаимодействия с пользователем
"""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class Keyboards:
    """Класс с клавиатурами бота"""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню бота"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(KeyboardButton("📩 Обращение в Совет"))
        markup.add(KeyboardButton("📝 Заявка на вступление в Совет"))
        markup.add(KeyboardButton("ℹ️ Информация о Совете"))
        markup.add(KeyboardButton("👥 Руководство Совета"))
        return markup

    @staticmethod
    def back_to_menu() -> ReplyKeyboardMarkup:
        """Кнопка возврата в меню"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("🔙 Вернуться в меню"))
        return markup

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        """Кнопка отмены"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("❌ Отменить"))
        return markup


# Создаем экземпляр класса для удобного использования
keyboards = Keyboards()

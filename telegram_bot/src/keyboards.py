# -*- coding: utf-8 -*-
"""
Модуль с клавиатурами бота
Содержит все клавиатуры для взаимодействия с пользователем
"""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    """Класс с клавиатурами бота"""

    @staticmethod
    def main_menu_inline() -> InlineKeyboardMarkup:
        """Главное меню бота (inline-кнопки)"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("📩 Обращение", callback_data="menu_appeal"),
            InlineKeyboardButton("📝 Заявка", callback_data="menu_application")
        )
        markup.row(
            InlineKeyboardButton("ℹ️ О Совете", callback_data="menu_info"),
            InlineKeyboardButton("👥 Руководство", callback_data="menu_leadership")
        )
        markup.row(
            InlineKeyboardButton("❓ FAQ", callback_data="menu_faq")
        )
        return markup

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню бота (обычные кнопки - для совместимости)"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(KeyboardButton("📩 Обращение в Совет"))
        markup.add(KeyboardButton("📝 Заявка на вступление в Совет"))
        markup.add(KeyboardButton("ℹ️ Информация о Совете"))
        markup.add(KeyboardButton("👥 Руководство Совета"))
        markup.add(KeyboardButton("❓ FAQ"))
        return markup

    @staticmethod
    def back_to_menu_inline() -> InlineKeyboardMarkup:
        """Кнопка возврата в меню (inline)"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu"))
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

    @staticmethod
    def cancel_inline() -> InlineKeyboardMarkup:
        """Кнопка отмены (inline)"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
        return markup


# Создаем экземпляр класса для удобного использования
keyboards = Keyboards()

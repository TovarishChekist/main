"""Клавиатуры для бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✍️ Подать обращение"),
        KeyboardButton(text="📊 Мои обращения")
    )
    builder.row(
        KeyboardButton(text="ℹ️ Информация"),
        KeyboardButton(text="❓ Помощь")
    )
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Все обращения"),
        KeyboardButton(text="🆕 Новые обращения")
    )
    builder.row(
        KeyboardButton(text="📈 Статистика"),
        KeyboardButton(text="👤 Пользовательское меню")
    )
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_appeal_actions(appeal_id: int) -> InlineKeyboardMarkup:
    """Действия с обращением"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Обработано",
            callback_data=f"status_processed_{appeal_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Подробнее",
            callback_data=f"detail_{appeal_id}"
        )
    )
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back"))
    return builder.as_markup()

"""Клавиатуры бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Отправить обращение", callback_data="new_appeal")],
        [InlineKeyboardButton(text="📋 Мои обращения", callback_data="my_appeals")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")]
    ])
    return keyboard

def get_cancel_keyboard():
    """Кнопка отмены"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить")]],
        resize_keyboard=True
    )
    return keyboard

def get_back_to_menu():
    """Кнопка возврата в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="main_menu")]
    ])
    return keyboard

def get_appeal_actions(appeal_id: int):
    """Действия с обращением для администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять в работу", callback_data=f"accept_{appeal_id}")],
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{appeal_id}")],
        [InlineKeyboardButton(text="📋 Закрыть", callback_data=f"close_{appeal_id}")]
    ])
    return keyboard

def get_status_keyboard(appeal_id: int):
    """Клавиатура для просмотра статуса обращения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статус", callback_data=f"status_{appeal_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    return keyboard

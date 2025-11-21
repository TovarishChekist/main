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

# Админские клавиатуры

def get_admin_menu():
    """Главное меню администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🆕 Новые обращения", callback_data="admin_new")],
        [InlineKeyboardButton(text="⏳ В работе", callback_data="admin_in_progress")],
        [InlineKeyboardButton(text="✅ Закрытые", callback_data="admin_closed")],
        [InlineKeyboardButton(text="📋 Все обращения", callback_data="admin_all")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search")],
        [InlineKeyboardButton(text="💾 Экспорт данных", callback_data="admin_export")],
        [InlineKeyboardButton(text="🗑️ Очистка логов", callback_data="admin_cleanup")]
    ])
    return keyboard

def get_admin_back():
    """Кнопка возврата в админ-панель"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_panel")]
    ])
    return keyboard

def get_appeal_detail_admin(appeal_id: int):
    """Детальный просмотр обращения для админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{appeal_id}")],
        [InlineKeyboardButton(text="✅ Принять в работу", callback_data=f"accept_{appeal_id}")],
        [InlineKeyboardButton(text="📋 Закрыть", callback_data=f"close_{appeal_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_appeal_{appeal_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    return keyboard

def get_pagination_keyboard(callback_prefix: str, page: int, total_pages: int):
    """Клавиатура с пагинацией"""
    buttons = []

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{callback_prefix}_page_{page-1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{callback_prefix}_page_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка возврата
    buttons.append([InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quick_replies():
    """Быстрые ответы для админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Спасибо за обращение", callback_data="quick_thanks")],
        [InlineKeyboardButton(text="⏳ Обращение в работе", callback_data="quick_in_progress")],
        [InlineKeyboardButton(text="📋 Обращение рассмотрено", callback_data="quick_reviewed")],
        [InlineKeyboardButton(text="✏️ Написать своё", callback_data="quick_custom")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]
    ])
    return keyboard

def get_search_result_actions(appeal_id: int):
    """Действия с результатом поиска"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ Подробнее", callback_data=f"view_{appeal_id}")],
        [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="admin_search")]
    ])
    return keyboard

def get_cleanup_menu():
    """Меню очистки логов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Удалить закрытые", callback_data="cleanup_closed")],
        [InlineKeyboardButton(text="📅 Старше 30 дней", callback_data="cleanup_30days")],
        [InlineKeyboardButton(text="📅 Старше 60 дней", callback_data="cleanup_60days")],
        [InlineKeyboardButton(text="📅 Старше 90 дней", callback_data="cleanup_90days")],
        [InlineKeyboardButton(text="⚠️ Удалить ВСЁ", callback_data="cleanup_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    return keyboard

def get_cleanup_confirm(action: str):
    """Подтверждение удаления"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"cleanup_confirm_{action}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cleanup")]
    ])
    return keyboard

def get_delete_appeal_button(appeal_id: int):
    """Кнопка удаления конкретного обращения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{appeal_id}")],
        [InlineKeyboardButton(text="✅ Принять в работу", callback_data=f"accept_{appeal_id}")],
        [InlineKeyboardButton(text="📋 Закрыть", callback_data=f"close_{appeal_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_appeal_{appeal_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    return keyboard

"""Обработчики команд и сообщений"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database.db import (
    create_appeal, get_user_appeals, get_appeal,
    update_appeal_status, add_admin_response, get_new_appeals,
    get_statistics, get_appeals_by_status, get_all_appeals,
    count_appeals_by_status, count_all_appeals, search_appeals,
    export_appeals_to_text
)
from bot.keyboards import (
    get_main_menu, get_cancel_keyboard, get_back_to_menu,
    get_appeal_actions, get_status_keyboard, get_admin_menu,
    get_admin_back, get_appeal_detail_admin, get_pagination_keyboard,
    get_quick_replies, get_search_result_actions
)
from bot.config import ADMIN_ID

router = Router()

# Состояния для FSM
class AppealStates(StatesGroup):
    waiting_for_message = State()

class AdminStates(StatesGroup):
    waiting_for_response = State()
    waiting_for_search = State()

# Форматирование статуса
def format_status(status: str) -> str:
    """Форматирование статуса обращения"""
    statuses = {
        'new': '🆕 Новое',
        'in_progress': '⏳ В работе',
        'closed': '✅ Закрыто'
    }
    return statuses.get(status, status)

# Форматирование даты
def format_date(date_str: str) -> str:
    """Форматирование даты"""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return date_str

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это бот для приёма обращений к <b>Председателю Совета Первых</b> "
        "Первичного отделения «Движения первых».\n\n"
        "📌 Здесь вы можете:\n"
        "• Отправить своё обращение\n"
        "• Отслеживать статус обращений\n"
        "• Получать ответы на свои вопросы\n\n"
        "Выберите действие из меню ниже:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню"""
    await state.clear()

    welcome_text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите необходимое действие:"
    )

    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "new_appeal")
async def start_new_appeal(callback: CallbackQuery, state: FSMContext):
    """Начало создания нового обращения"""
    text = (
        "📝 <b>Новое обращение</b>\n\n"
        "Пожалуйста, напишите ваше обращение.\n\n"
        "💡 <i>Постарайтесь изложить суть вопроса максимально чётко и подробно.</i>\n\n"
        "Используйте кнопку ниже для отмены."
    )

    await callback.message.answer(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AppealStates.waiting_for_message)
    await callback.answer()

@router.message(F.text == "❌ Отменить")
async def cancel_action(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await message.answer(
        "❌ Действие отменено",
        reply_markup=None
    )

    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.message(AppealStates.waiting_for_message)
async def process_appeal_message(message: Message, state: FSMContext):
    """Обработка текста обращения"""
    # Создаём обращение в БД
    appeal_id = await create_appeal(
        user_id=message.from_user.id,
        username=message.from_user.username or "Не указан",
        full_name=message.from_user.full_name,
        message=message.text
    )

    await state.clear()

    # Уведомление пользователю
    confirmation_text = (
        "✅ <b>Обращение успешно отправлено!</b>\n\n"
        f"📋 Номер обращения: <code>#{appeal_id}</code>\n\n"
        "Ваше обращение будет рассмотрено Председателем Совета Первых. "
        "Вы получите уведомление, когда поступит ответ.\n\n"
        "Вы можете отслеживать статус в разделе \"Мои обращения\"."
    )

    await message.answer(
        confirmation_text,
        reply_markup=get_back_to_menu(),
        parse_mode="HTML"
    )

    # Уведомление администратору
    admin_text = (
        "🔔 <b>Новое обращение!</b>\n\n"
        f"📋 Номер: <code>#{appeal_id}</code>\n"
        f"👤 От: {message.from_user.full_name}\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n"
        f"📱 Username: @{message.from_user.username or 'не указан'}\n\n"
        f"💬 <b>Текст обращения:</b>\n{message.text}"
    )

    try:
        await message.bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=get_appeal_actions(appeal_id),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")

@router.callback_query(F.data == "my_appeals")
async def show_my_appeals(callback: CallbackQuery):
    """Показать обращения пользователя"""
    appeals = await get_user_appeals(callback.from_user.id)

    if not appeals:
        text = (
            "📋 <b>Мои обращения</b>\n\n"
            "У вас пока нет обращений.\n\n"
            "Вы можете создать новое обращение, нажав на соответствующую кнопку в главном меню."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_menu(),
            parse_mode="HTML"
        )
    else:
        text = "📋 <b>Ваши обращения:</b>\n\n"

        for appeal in appeals[:10]:  # Показываем последние 10
            status = format_status(appeal['status'])
            date = format_date(appeal['created_at'])

            text += (
                f"━━━━━━━━━━━━━━━\n"
                f"📌 Обращение <code>#{appeal['id']}</code>\n"
                f"📅 Дата: {date}\n"
                f"📊 Статус: {status}\n"
                f"💬 Текст: {appeal['message'][:100]}{'...' if len(appeal['message']) > 100 else ''}\n"
            )

            if appeal['response']:
                text += f"✉️ <b>Ответ получен</b>\n"

            text += "\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_menu(),
            parse_mode="HTML"
        )

    await callback.answer()

@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Информация о боте"""
    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "Этот бот создан для приёма обращений к Председателю Совета Первых "
        "Первичного отделения «Движения первых».\n\n"
        "🎯 <b>Наша цель:</b>\n"
        "Обеспечить удобную и быструю связь между участниками движения и руководством.\n\n"
        "📱 <b>Как пользоваться:</b>\n"
        "1. Нажмите \"Отправить обращение\"\n"
        "2. Опишите свой вопрос или предложение\n"
        "3. Ожидайте ответа от Председателя\n\n"
        "💙 Движение Первых - создаём будущее вместе!"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# Админские команды
@router.callback_query(F.data.startswith("accept_"))
async def accept_appeal(callback: CallbackQuery):
    """Принять обращение в работу"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    appeal_id = int(callback.data.split("_")[1])
    await update_appeal_status(appeal_id, "in_progress")

    appeal = await get_appeal(appeal_id)

    # Уведомление пользователю
    try:
        await callback.bot.send_message(
            appeal['user_id'],
            f"⏳ Ваше обращение <code>#{appeal_id}</code> принято в работу!",
            parse_mode="HTML"
        )
    except:
        pass

    await callback.answer("✅ Обращение принято в работу!")

    # Обновляем сообщение
    text = callback.message.text + "\n\n⏳ <b>Статус: В работе</b>"
    await callback.message.edit_text(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    """Начать ответ на обращение"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    appeal_id = int(callback.data.split("_")[1])
    await state.update_data(appeal_id=appeal_id)
    await state.set_state(AdminStates.waiting_for_response)

    await callback.message.answer(
        "✏️ Напишите ответ на обращение:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_response)
async def process_admin_response(message: Message, state: FSMContext):
    """Обработка ответа администратора"""
    if message.text == "❌ Отменить":
        await cancel_action(message, state)
        return

    data = await state.get_data()
    appeal_id = data['appeal_id']

    await add_admin_response(appeal_id, message.text)
    await state.clear()

    appeal = await get_appeal(appeal_id)

    # Отправка ответа пользователю
    user_text = (
        f"✉️ <b>Получен ответ на обращение #{appeal_id}</b>\n\n"
        f"📝 <b>Ваше обращение:</b>\n{appeal['message']}\n\n"
        f"💬 <b>Ответ:</b>\n{message.text}"
    )

    try:
        await message.bot.send_message(
            appeal['user_id'],
            user_text,
            parse_mode="HTML"
        )
        await message.answer(
            "✅ Ответ отправлен пользователю!",
            reply_markup=None
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка отправки ответа: {e}",
            reply_markup=None
        )

@router.callback_query(F.data.startswith("close_"))
async def close_appeal(callback: CallbackQuery):
    """Закрыть обращение"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    appeal_id = int(callback.data.split("_")[1])
    await update_appeal_status(appeal_id, "closed")

    await callback.answer("✅ Обращение закрыто!")

    text = callback.message.text + "\n\n✅ <b>Статус: Закрыто</b>"
    await callback.message.edit_text(text, parse_mode="HTML")

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Расширенная админ-панель"""
    if message.from_user.id != ADMIN_ID:
        return

    stats = await get_statistics()

    text = (
        "👑 <b>Панель администратора</b>\n\n"
        "📊 <b>Статистика:</b>\n"
        f"• Всего обращений: {stats['total']}\n"
        f"• 🆕 Новых: {stats['new']}\n"
        f"• ⏳ В работе: {stats['in_progress']}\n"
        f"• ✅ Закрытых: {stats['closed']}\n\n"
        f"📅 За сегодня: {stats['today']}\n"
        f"📅 За неделю: {stats['week']}\n"
        f"📅 За месяц: {stats['month']}\n\n"
        "Выберите действие из меню ниже:"
    )

    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Показать админ-панель"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    await state.clear()
    stats = await get_statistics()

    text = (
        "👑 <b>Панель администратора</b>\n\n"
        "📊 <b>Статистика:</b>\n"
        f"• Всего обращений: {stats['total']}\n"
        f"• 🆕 Новых: {stats['new']}\n"
        f"• ⏳ В работе: {stats['in_progress']}\n"
        f"• ✅ Закрытых: {stats['closed']}\n\n"
        f"📅 За сегодня: {stats['today']}\n"
        f"📅 За неделю: {stats['week']}\n"
        f"📅 За месяц: {stats['month']}\n\n"
        "Выберите действие из меню ниже:"
    )

    await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    await callback.answer()

# Расширенные функции админ-панели

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Подробная статистика"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    stats = await get_statistics()

    text = (
        "📊 <b>Подробная статистика</b>\n\n"
        f"📈 <b>Общие показатели:</b>\n"
        f"• Всего обращений: <code>{stats['total']}</code>\n\n"
        f"📋 <b>По статусам:</b>\n"
        f"• 🆕 Новых: <code>{stats['new']}</code>\n"
        f"• ⏳ В работе: <code>{stats['in_progress']}</code>\n"
        f"• ✅ Закрытых: <code>{stats['closed']}</code>\n\n"
        f"📅 <b>По периодам:</b>\n"
        f"• Сегодня: <code>{stats['today']}</code>\n"
        f"• За неделю: <code>{stats['week']}</code>\n"
        f"• За месяц: <code>{stats['month']}</code>\n\n"
    )

    # Подсчёт процентов
    if stats['total'] > 0:
        closed_percent = round(stats['closed'] / stats['total'] * 100, 1)
        text += f"✅ Закрыто от общего: <b>{closed_percent}%</b>\n"

    await callback.message.edit_text(text, reply_markup=get_admin_back(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_new")
async def show_new_appeals(callback: CallbackQuery):
    """Новые обращения"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    await show_appeals_by_status(callback, "new", "🆕 Новые обращения", 0)

@router.callback_query(F.data == "admin_in_progress")
async def show_in_progress_appeals(callback: CallbackQuery):
    """Обращения в работе"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    await show_appeals_by_status(callback, "in_progress", "⏳ Обращения в работе", 0)

@router.callback_query(F.data == "admin_closed")
async def show_closed_appeals(callback: CallbackQuery):
    """Закрытые обращения"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    await show_appeals_by_status(callback, "closed", "✅ Закрытые обращения", 0)

@router.callback_query(F.data == "admin_all")
async def show_all_appeals(callback: CallbackQuery):
    """Все обращения"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    page = 0
    limit = 5
    appeals = await get_all_appeals(limit=limit, offset=page * limit)
    total_count = await count_all_appeals()
    total_pages = (total_count + limit - 1) // limit

    if not appeals:
        text = "📋 <b>Все обращения</b>\n\nОбращений пока нет."
        await callback.message.edit_text(text, reply_markup=get_admin_back(), parse_mode="HTML")
        await callback.answer()
        return

    text = f"📋 <b>Все обращения</b>\n\nВсего: {total_count}\n\n"

    for appeal in appeals:
        status = format_status(appeal['status'])
        date = format_date(appeal['created_at'])
        text += (
            f"━━━━━━━━━━━━━━━\n"
            f"📌 Обращение <code>#{appeal['id']}</code>\n"
            f"👤 {appeal['full_name']}\n"
            f"📅 {date}\n"
            f"📊 Статус: {status}\n"
            f"💬 {appeal['message'][:80]}{'...' if len(appeal['message']) > 80 else ''}\n\n"
        )

    keyboard = get_pagination_keyboard("admin_all", page, total_pages)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def show_appeals_by_status(callback: CallbackQuery, status: str, title: str, page: int):
    """Универсальная функция для показа обращений по статусу"""
    limit = 5
    appeals = await get_appeals_by_status(status, limit=limit, offset=page * limit)
    total_count = await count_appeals_by_status(status)
    total_pages = max(1, (total_count + limit - 1) // limit)

    if not appeals:
        text = f"{title}\n\nОбращений с таким статусом нет."
        await callback.message.edit_text(text, reply_markup=get_admin_back(), parse_mode="HTML")
        await callback.answer()
        return

    text = f"{title}\n\nВсего: {total_count}\n\n"

    for appeal in appeals:
        date = format_date(appeal['created_at'])
        text += (
            f"━━━━━━━━━━━━━━━\n"
            f"📌 <code>#{appeal['id']}</code> | {appeal['full_name']}\n"
            f"📅 {date}\n"
            f"💬 {appeal['message'][:80]}{'...' if len(appeal['message']) > 80 else ''}\n\n"
        )

    callback_prefix = f"admin_{status}"
    keyboard = get_pagination_keyboard(callback_prefix, page, total_pages)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Обработчики пагинации
@router.callback_query(F.data.regexp(r"admin_(new|in_progress|closed)_page_\d+"))
async def handle_status_pagination(callback: CallbackQuery):
    """Обработка пагинации по статусам"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    # Парсинг callback_data
    parts = callback.data.split("_")
    if parts[1] == "in":  # admin_in_progress_page_N
        status = "in_progress"
        page = int(parts[4])
        title = "⏳ Обращения в работе"
    else:
        status = parts[1]  # new или closed
        page = int(parts[3])
        if status == "new":
            title = "🆕 Новые обращения"
        else:
            title = "✅ Закрытые обращения"

    await show_appeals_by_status(callback, status, title, page)

@router.callback_query(F.data.regexp(r"admin_all_page_\d+"))
async def handle_all_pagination(callback: CallbackQuery):
    """Обработка пагинации всех обращений"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    limit = 5
    appeals = await get_all_appeals(limit=limit, offset=page * limit)
    total_count = await count_all_appeals()
    total_pages = (total_count + limit - 1) // limit

    text = f"📋 <b>Все обращения</b>\n\nВсего: {total_count}\n\n"

    for appeal in appeals:
        status = format_status(appeal['status'])
        date = format_date(appeal['created_at'])
        text += (
            f"━━━━━━━━━━━━━━━\n"
            f"📌 Обращение <code>#{appeal['id']}</code>\n"
            f"👤 {appeal['full_name']}\n"
            f"📅 {date}\n"
            f"📊 Статус: {status}\n"
            f"💬 {appeal['message'][:80]}{'...' if len(appeal['message']) > 80 else ''}\n\n"
        )

    keyboard = get_pagination_keyboard("admin_all", page, total_pages)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Поиск обращений
@router.callback_query(F.data == "admin_search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск обращений"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    text = (
        "🔍 <b>Поиск обращений</b>\n\n"
        "Введите текст для поиска:\n"
        "• ID обращения (например: 123)\n"
        "• Имя пользователя\n"
        "• Текст обращения\n\n"
        "Для отмены используйте кнопку ниже."
    )

    await callback.message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_search)
    await callback.answer()

@router.message(AdminStates.waiting_for_search)
async def process_search(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    if message.text == "❌ Отменить":
        await cancel_action(message, state)
        return

    query = message.text.strip()

    # Попытка поиска по ID
    if query.isdigit():
        appeal = await get_appeal(int(query))
        if appeal:
            appeals = [appeal]
        else:
            appeals = []
    else:
        appeals = await search_appeals(query)

    await state.clear()

    if not appeals:
        text = f"🔍 <b>Результаты поиска</b>\n\nПо запросу «{query}» ничего не найдено."
        await message.answer(text, reply_markup=get_admin_back(), parse_mode="HTML")
        return

    text = f"🔍 <b>Результаты поиска</b>\n\nПо запросу «{query}» найдено: {len(appeals)}\n\n"

    for appeal in appeals[:10]:  # Показываем первые 10
        status = format_status(appeal['status'])
        date = format_date(appeal['created_at'])
        text += (
            f"━━━━━━━━━━━━━━━\n"
            f"📌 <code>#{appeal['id']}</code> | {appeal['full_name']}\n"
            f"📅 {date} | {status}\n"
            f"💬 {appeal['message'][:100]}{'...' if len(appeal['message']) > 100 else ''}\n\n"
        )

    if len(appeals) > 10:
        text += f"\n<i>Показано первые 10 из {len(appeals)} результатов</i>"

    await message.answer(text, reply_markup=get_admin_back(), parse_mode="HTML")

# Экспорт данных
@router.callback_query(F.data == "admin_export")
async def export_data(callback: CallbackQuery):
    """Экспорт всех обращений в текстовый файл"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    await callback.answer("📥 Экспортирую данные...")

    text_data = await export_appeals_to_text()

    # Отправка файла
    from aiogram.types import BufferedInputFile
    from datetime import datetime

    filename = f"appeals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    file = BufferedInputFile(text_data.encode('utf-8'), filename=filename)

    await callback.message.answer_document(
        file,
        caption="📄 <b>Экспорт обращений</b>\n\nВсе обращения выгружены в файл.",
        parse_mode="HTML"
    )

    await callback.message.answer(
        "✅ Экспорт завершён!",
        reply_markup=get_admin_back()
    )

# Обработчик для "пустого" callback (для кнопки с номером страницы)
@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик пустого действия"""
    await callback.answer()

# Детальный просмотр обращения
@router.callback_query(F.data.startswith("view_"))
async def view_appeal_detail(callback: CallbackQuery):
    """Детальный просмотр обращения"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    appeal_id = int(callback.data.split("_")[1])
    appeal = await get_appeal(appeal_id)

    if not appeal:
        await callback.answer("Обращение не найдено", show_alert=True)
        return

    status = format_status(appeal['status'])
    date = format_date(appeal['created_at'])

    text = (
        f"📌 <b>Обращение #{appeal['id']}</b>\n\n"
        f"👤 <b>От:</b> {appeal['full_name']}\n"
        f"🆔 <b>User ID:</b> <code>{appeal['user_id']}</code>\n"
        f"📱 <b>Username:</b> @{appeal['username'] or 'не указан'}\n"
        f"📅 <b>Дата:</b> {date}\n"
        f"📊 <b>Статус:</b> {status}\n\n"
        f"💬 <b>Текст обращения:</b>\n{appeal['message']}\n"
    )

    if appeal['response']:
        response_date = format_date(appeal['admin_response_at'])
        text += (
            f"\n━━━━━━━━━━━━━━━\n"
            f"✉️ <b>Ответ администратора:</b>\n{appeal['response']}\n"
            f"📅 <b>Дата ответа:</b> {response_date}\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_appeal_detail_admin(appeal_id),
        parse_mode="HTML"
    )
    await callback.answer()

"""Обработчики команд и сообщений"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database.db import (
    create_appeal, get_user_appeals, get_appeal,
    update_appeal_status, add_admin_response, get_new_appeals
)
from bot.keyboards import (
    get_main_menu, get_cancel_keyboard, get_back_to_menu,
    get_appeal_actions, get_status_keyboard
)
from bot.config import ADMIN_ID

router = Router()

# Состояния для FSM
class AppealStates(StatesGroup):
    waiting_for_message = State()

class AdminStates(StatesGroup):
    waiting_for_response = State()

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
    """Админ-панель"""
    if message.from_user.id != ADMIN_ID:
        return

    new_appeals = await get_new_appeals()

    text = (
        "👑 <b>Панель администратора</b>\n\n"
        f"🆕 Новых обращений: {len(new_appeals)}\n\n"
    )

    if new_appeals:
        text += "<b>Последние обращения:</b>\n\n"
        for appeal in new_appeals[:5]:
            date = format_date(appeal['created_at'])
            text += (
                f"📌 #{appeal['id']} | {date}\n"
                f"👤 {appeal['full_name']}\n"
                f"💬 {appeal['message'][:50]}...\n\n"
            )

    await message.answer(text, parse_mode="HTML")

"""
Telegram бот для приёма обращений Председателю Совета Первых
Первичного отделения «Движения первых»
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from datetime import datetime

import config
from database import Database
from keyboards import (
    get_main_menu,
    get_admin_menu,
    get_cancel_keyboard,
    get_appeal_actions,
    get_back_keyboard
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
db = Database()


# Состояния для FSM
class AppealStates(StatesGroup):
    waiting_for_appeal = State()


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_name = message.from_user.full_name
    is_admin = message.from_user.id in config.ADMIN_IDS

    welcome_text = f"""
🎉 <b>Добро пожаловать, {user_name}!</b>

Это официальный бот для приёма обращений к <b>Председателю Совета Первых</b> Первичного отделения «Движения первых».

<b>Что вы можете сделать:</b>
✍️ Подать обращение
📊 Просмотреть свои обращения
ℹ️ Узнать информацию о движении
❓ Получить помощь

<i>Выберите нужное действие в меню ниже.</i>
"""

    if is_admin:
        welcome_text += "\n\n🔑 <b>Вы вошли как администратор</b>"
        await message.answer(welcome_text, reply_markup=get_admin_menu(), parse_mode="HTML")
    else:
        await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
❓ <b>Помощь по использованию бота</b>

<b>Доступные команды:</b>
/start - Начать работу с ботом
/help - Показать это сообщение

<b>Как подать обращение:</b>
1️⃣ Нажмите кнопку "✍️ Подать обращение"
2️⃣ Напишите ваше обращение в одном сообщении
3️⃣ Отправьте сообщение
4️⃣ Получите подтверждение

<b>Внимание:</b>
• Обращение должно быть корректным и уважительным
• Избегайте нецензурной лексики
• Формулируйте вопрос чётко и конкретно

<b>Ваше обращение будет рассмотрено в ближайшее время!</b>
"""
    await message.answer(help_text, parse_mode="HTML")


# ==================== ГЛАВНОЕ МЕНЮ ====================

@dp.message(F.text == "✍️ Подать обращение")
async def new_appeal(message: Message, state: FSMContext):
    """Начало подачи обращения"""
    await message.answer(
        "📝 <b>Подача обращения</b>\n\n"
        "Пожалуйста, напишите ваше обращение одним сообщением.\n\n"
        "<i>Постарайтесь изложить суть вопроса чётко и понятно.</i>\n\n"
        "Для отмены нажмите кнопку ниже.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AppealStates.waiting_for_appeal)


@dp.message(F.text == "📊 Мои обращения")
async def my_appeals(message: Message):
    """Просмотр обращений пользователя"""
    appeals = await db.get_all_appeals()
    user_appeals = [a for a in appeals if a['user_id'] == message.from_user.id]

    if not user_appeals:
        await message.answer(
            "📭 <b>У вас пока нет обращений</b>\n\n"
            "Вы можете подать обращение, нажав кнопку "
            "\"✍️ Подать обращение\"",
            parse_mode="HTML"
        )
        return

    text = "📊 <b>Ваши обращения:</b>\n\n"
    for appeal in user_appeals[:10]:  # Показываем последние 10
        status_emoji = "🆕" if appeal['status'] == 'new' else "✅"
        created = datetime.fromisoformat(appeal['created_at']).strftime("%d.%m.%Y %H:%M")
        appeal_preview = appeal['appeal_text'][:50] + "..." if len(appeal['appeal_text']) > 50 else appeal['appeal_text']

        text += f"{status_emoji} <b>Обращение #{appeal['id']}</b>\n"
        text += f"📅 {created}\n"
        text += f"📝 {appeal_preview}\n"
        text += f"Статус: {'Новое' if appeal['status'] == 'new' else 'Обработано'}\n\n"

    if len(user_appeals) > 10:
        text += f"<i>Показаны последние 10 из {len(user_appeals)} обращений</i>"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "ℹ️ Информация")
async def info(message: Message):
    """Информация о движении"""
    info_text = """
ℹ️ <b>О Движении Первых</b>

<b>Российское движение детей и молодёжи «Движение Первых»</b> —
это крупнейшее в России молодёжное движение, созданное для
всестороннего развития детей и молодёжи.

<b>Наши ценности:</b>
🔹 Дружба
🔹 Активная жизненная позиция
🔹 Здоровый образ жизни
🔹 Созидание и творчество
🔹 Патриотизм

<b>Председатель Совета Первых</b> — это лидер первичного отделения,
который координирует деятельность и представляет интересы участников.

<b>Вы можете обратиться с вопросами о:</b>
• Работе первичного отделения
• Участии в мероприятиях
• Предложениях и инициативах
• Решении организационных вопросов
"""
    await message.answer(info_text, parse_mode="HTML")


@dp.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    """Кнопка помощи"""
    await cmd_help(message)


# ==================== ОБРАБОТКА ОБРАЩЕНИЯ ====================

@dp.message(AppealStates.waiting_for_appeal, F.text == "❌ Отмена")
async def cancel_appeal(message: Message, state: FSMContext):
    """Отмена подачи обращения"""
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    keyboard = get_admin_menu() if is_admin else get_main_menu()

    await message.answer(
        "❌ <b>Подача обращения отменена</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(AppealStates.waiting_for_appeal)
async def process_appeal(message: Message, state: FSMContext):
    """Обработка текста обращения"""
    appeal_text = message.text

    # Проверка длины обращения
    if len(appeal_text) < 10:
        await message.answer(
            "⚠️ <b>Обращение слишком короткое</b>\n\n"
            "Пожалуйста, опишите вашу проблему более подробно (минимум 10 символов).",
            parse_mode="HTML"
        )
        return

    if len(appeal_text) > 4000:
        await message.answer(
            "⚠️ <b>Обращение слишком длинное</b>\n\n"
            "Пожалуйста, сократите текст до 4000 символов.",
            parse_mode="HTML"
        )
        return

    # Сохранение обращения
    appeal_id = await db.add_appeal(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        appeal_text=appeal_text
    )

    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    keyboard = get_admin_menu() if is_admin else get_main_menu()

    # Подтверждение пользователю
    await message.answer(
        f"✅ <b>Обращение успешно отправлено!</b>\n\n"
        f"📋 Номер обращения: <code>#{appeal_id}</code>\n\n"
        f"Ваше обращение будет рассмотрено Председателем Совета Первых "
        f"в ближайшее время.\n\n"
        f"<i>Спасибо за обращение!</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # Уведомление администраторам
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 <b>Новое обращение #{appeal_id}</b>\n\n"
                f"👤 От: {message.from_user.full_name}\n"
                f"🆔 User ID: <code>{message.from_user.id}</code>\n"
                f"📱 Username: @{message.from_user.username or 'нет'}\n\n"
                f"📝 <b>Текст обращения:</b>\n{appeal_text}",
                reply_markup=get_appeal_actions(appeal_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")


# ==================== АДМИН-ПАНЕЛЬ ====================

@dp.message(F.text == "📋 Все обращения")
async def all_appeals(message: Message):
    """Все обращения (только для админов)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещён")
        return

    appeals = await db.get_all_appeals()

    if not appeals:
        await message.answer(
            "📭 <b>Обращений пока нет</b>",
            parse_mode="HTML"
        )
        return

    text = "📋 <b>Все обращения:</b>\n\n"
    for appeal in appeals[:15]:
        status_emoji = "🆕" if appeal['status'] == 'new' else "✅"
        created = datetime.fromisoformat(appeal['created_at']).strftime("%d.%m.%Y %H:%M")
        appeal_preview = appeal['appeal_text'][:40] + "..." if len(appeal['appeal_text']) > 40 else appeal['appeal_text']

        text += f"{status_emoji} <b>#{appeal['id']}</b> от {appeal['full_name']}\n"
        text += f"📅 {created}\n"
        text += f"📝 {appeal_preview}\n\n"

    if len(appeals) > 15:
        text += f"<i>Показаны последние 15 из {len(appeals)}</i>"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🆕 Новые обращения")
async def new_appeals(message: Message):
    """Новые обращения (только для админов)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещён")
        return

    appeals = await db.get_all_appeals()
    new_appeals_list = [a for a in appeals if a['status'] == 'new']

    if not new_appeals_list:
        await message.answer(
            "✅ <b>Новых обращений нет</b>\n\n"
            "Все обращения обработаны!",
            parse_mode="HTML"
        )
        return

    text = f"🆕 <b>Новые обращения ({len(new_appeals_list)}):</b>\n\n"
    for appeal in new_appeals_list[:10]:
        created = datetime.fromisoformat(appeal['created_at']).strftime("%d.%m.%Y %H:%M")

        text += f"<b>Обращение #{appeal['id']}</b>\n"
        text += f"👤 {appeal['full_name']} (@{appeal['username'] or 'нет'})\n"
        text += f"📅 {created}\n"
        text += f"📝 {appeal['appeal_text'][:100]}...\n\n"

    if len(new_appeals_list) > 10:
        text += f"<i>Показаны 10 из {len(new_appeals_list)}</i>"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📈 Статистика")
async def statistics(message: Message):
    """Статистика (только для админов)"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещён")
        return

    stats = await db.get_stats()

    text = f"""
📈 <b>Статистика обращений</b>

📊 Всего обращений: <b>{stats['total']}</b>
🆕 Новых: <b>{stats['new']}</b>
✅ Обработано: <b>{stats['processed']}</b>

<i>Данные на {datetime.now().strftime("%d.%m.%Y %H:%M")}</i>
"""
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "👤 Пользовательское меню")
async def user_menu_admin(message: Message):
    """Переключение на пользовательское меню"""
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔️ Доступ запрещён")
        return

    await message.answer(
        "👤 <b>Пользовательское меню</b>\n\n"
        "Вы переключились в обычный режим.\n"
        "Для возврата в админ-панель используйте /start",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


# ==================== CALLBACK QUERIES ====================

@dp.callback_query(F.data.startswith("status_processed_"))
async def process_status_callback(callback: CallbackQuery):
    """Обработка callback для смены статуса"""
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔️ Доступ запрещён", show_alert=True)
        return

    appeal_id = int(callback.data.split("_")[-1])
    await db.update_status(appeal_id, 'processed')

    await callback.answer("✅ Обращение отмечено как обработанное")
    await callback.message.edit_reply_markup(reply_markup=None)


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")

    # Инициализация базы данных
    await db.init_db()
    logger.info("База данных инициализирована")

    # Запуск polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

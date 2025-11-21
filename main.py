"""
Telegram бот для приёма обращений Председателю Совета Первых
Первичного отделения «Движения первых»
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher

# Проверка версии aiogram и импорт соответствующих модулей
try:
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    AIOGRAM_3 = True
except ImportError:
    # Для aiogram 2.x
    AIOGRAM_3 = False

from bot.config import BOT_TOKEN
from bot.handlers import router
from database.db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована")

    # Создание бота и диспетчера
    if AIOGRAM_3:
        # aiogram 3.x
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()
        dp.include_router(router)

        logger.info("Бот запущен и готов к работе! (aiogram 3.x)")
        logger.info("Нажмите Ctrl+C для остановки")

        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()
    else:
        # aiogram 2.x
        from aiogram import types
        bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
        dp = Dispatcher(bot)
        dp.include_router(router)

        logger.info("Бот запущен и готов к работе! (aiogram 2.x)")
        logger.info("Нажмите Ctrl+C для остановки")

        try:
            await dp.start_polling()
        finally:
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

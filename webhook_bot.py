"""
Webhook версия бота для PythonAnywhere и других WSGI хостингов
"""
import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Загрузка переменных окружения
load_dotenv()

# Импорт обработчиков из основного бота
sys.path.insert(0, os.path.dirname(__file__))

from bot import dp, bot, TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Webhook настройки
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-username.pythonanywhere.com/webhook')
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 8000


async def on_startup(app: web.Application):
    """Действия при запуске приложения"""
    webhook_info = await bot.get_webhook_info()

    # Если webhook не установлен или URL отличается
    if webhook_info.url != WEBHOOK_URL:
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        logger.info("Webhook set successfully")
    else:
        logger.info(f"Webhook already set to {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    """Действия при остановке приложения"""
    logger.info("Shutting down...")
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def create_app():
    """Создание WSGI приложения"""
    app = web.Application()

    # Настройка webhook обработчика
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)

    # Добавление startup/shutdown хуков
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Health check endpoint
    async def health(request):
        return web.Response(text="OK")

    app.router.add_get('/health', health)
    app.router.add_get('/', health)

    return app


# Для PythonAnywhere WSGI
application = create_app()


# Для локального запуска
if __name__ == '__main__':
    app = create_app()
    web.run_app(
        app,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT
    )

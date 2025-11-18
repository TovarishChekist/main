#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной файл запуска бота
Детский и Молодёжный Общественный Совет при Уполномоченном по правам ребёнка в Амурской области
"""

import sys
import logging
import signal
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

import telebot
from telebot import apihelper

from src.config import config
from src.handlers import BotHandlers

# Глобальная переменная для бота
bot = None

logger = logging.getLogger(__name__)


def setup_bot():
    """Настройка и инициализация бота"""
    global bot

    # Настройка логирования
    config.setup_logging()
    logger.info("=" * 60)
    logger.info("Запуск бота Детского и Молодёжного Общественного Совета")
    logger.info("=" * 60)

    # Проверка конфигурации
    if not config.validate():
        logger.critical("Ошибка валидации конфигурации. Проверьте файл .env")
        sys.exit(1)

    logger.info("Конфигурация успешно загружена")

    # Инициализация базы данных
    try:
        db = config.setup_database()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.critical(f"Ошибка при инициализации базы данных: {e}")
        sys.exit(1)

    # Настройка таймаутов API
    apihelper.CONNECT_TIMEOUT = config.CONNECT_TIMEOUT
    apihelper.READ_TIMEOUT = config.READ_TIMEOUT
    logger.info(f"Таймауты установлены: CONNECT={config.CONNECT_TIMEOUT}s, READ={config.READ_TIMEOUT}s")

    # Настройка прокси (если необходимо)
    if config.PROXY:
        apihelper.proxy = config.PROXY
        logger.info(f"Использование прокси: {config.PROXY}")

    # Создание бота
    try:
        bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode='HTML')
        logger.info("Бот успешно инициализирован")

        # Проверка подключения
        bot_info = bot.get_me()
        logger.info(f"Подключено как: @{bot_info.username} (ID: {bot_info.id})")

    except Exception as e:
        logger.critical(f"Ошибка при инициализации бота: {e}")
        sys.exit(1)

    # Регистрация обработчиков
    try:
        handlers = BotHandlers(bot, db)
        handlers.register_handlers()
        logger.info("Обработчики зарегистрированы успешно")
    except Exception as e:
        logger.critical(f"Ошибка при регистрации обработчиков: {e}")
        sys.exit(1)

    return bot


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}. Завершение работы бота...")
    if bot:
        bot.stop_polling()
    sys.exit(0)


def main():
    """Главная функция запуска бота"""
    global bot

    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Настройка и инициализация бота
    bot = setup_bot()

    # Запуск polling
    logger.info("Запуск polling...")
    logger.info("Бот готов к работе!")
    logger.info("Для остановки нажмите Ctrl+C")

    try:
        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            logger_level=logging.INFO,
            allowed_updates=None
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал KeyboardInterrupt")
    except Exception as e:
        logger.critical(f"Критическая ошибка в polling: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()

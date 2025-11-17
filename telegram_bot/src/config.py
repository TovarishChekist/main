# -*- coding: utf-8 -*-
"""
Модуль конфигурации бота
Содержит все настройки и параметры
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных окружения из .env файла
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Класс конфигурации бота"""

    # Токен бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')

    # ID чатов для пересылки
    APPEAL_CHAT_ID: int = int(os.getenv('APPEAL_CHAT_ID', '0'))
    APPLICATION_CHAT_ID: int = int(os.getenv('APPLICATION_CHAT_ID', '0'))

    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: Path = BASE_DIR / 'logs'
    LOG_FILE: Path = LOG_DIR / 'bot.log'

    # Настройки базы данных (для будущего расширения)
    DATABASE_PATH: Path = BASE_DIR / os.getenv('DATABASE_PATH', 'data/bot_data.db')

    # Таймауты API
    CONNECT_TIMEOUT: float = 15.0
    READ_TIMEOUT: float = 15.0

    # Прокси (опционально)
    PROXY: Optional[dict] = None  # {'https': 'socks5://localhost:9050'}

    # Валидация конфигурации
    @classmethod
    def validate(cls) -> bool:
        """Проверка корректности конфигурации"""
        errors = []

        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN не установлен")

        if not cls.APPEAL_CHAT_ID:
            errors.append("APPEAL_CHAT_ID не установлен")

        if not cls.APPLICATION_CHAT_ID:
            errors.append("APPLICATION_CHAT_ID не установлен")

        if errors:
            for error in errors:
                logging.error(f"Ошибка конфигурации: {error}")
            return False

        return True

    @classmethod
    def setup_logging(cls) -> None:
        """Настройка логирования"""
        # Создаем директорию для логов если её нет
        cls.LOG_DIR.mkdir(exist_ok=True)

        # Настройка формата логирования
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Настройка обработчиков
        handlers = [
            logging.FileHandler(cls.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]

        # Базовая настройка
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=log_format,
            datefmt=date_format,
            handlers=handlers
        )

        # Уменьшаем уровень логирования для telebot
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('telebot').setLevel(logging.INFO)


# Создаем экземпляр конфигурации
config = Config()

"""Конфигурация приложения"""
import os
from datetime import timedelta


class Config:
    """Базовая конфигурация"""
    # Secret key для сессий
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'council.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Файлы
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB максимальный размер файла
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads')

    # CORS
    CORS_HEADERS = 'Content-Type'


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для production"""
    DEBUG = False


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

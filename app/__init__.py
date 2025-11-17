"""Инициализация Flask приложения"""
from flask import Flask
from flask_cors import CORS
from config.config import Config


def create_app(config_class=Config):
    """Фабрика приложений Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Инициализация расширений
    from app.models import db
    db.init_app(app)
    CORS(app)

    # Регистрация blueprints
    from app.routes import (members_bp, events_bp, projects_bp,
                             documents_bp, reports_bp)

    app.register_blueprint(members_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(reports_bp)

    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()

    # Главная страница
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app

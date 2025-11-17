#!/usr/bin/env python3
"""Запуск Flask приложения системы управления Детским и Молодёжным Общественным Советом"""
import os
from app import create_app

# Создание приложения
app = create_app()

if __name__ == '__main__':
    # Запуск сервера
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

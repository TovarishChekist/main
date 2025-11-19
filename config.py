"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID администратора
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Дополнительные администраторы
ADDITIONAL_ADMINS = os.getenv('ADDITIONAL_ADMINS', '')
ADMIN_IDS = [ADMIN_ID]
if ADDITIONAL_ADMINS:
    ADMIN_IDS.extend([int(admin_id.strip()) for admin_id in ADDITIONAL_ADMINS.split(',')])

# База данных
DB_PATH = 'appeals.db'

"""Работа с базой данных"""
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional

DATABASE_PATH = "database/appeals.db"

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response TEXT,
                admin_response_at TIMESTAMP
            )
        """)
        await db.commit()

async def create_appeal(user_id: int, username: str, full_name: str, message: str) -> int:
    """Создание нового обращения"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO appeals (user_id, username, full_name, message)
               VALUES (?, ?, ?, ?)""",
            (user_id, username, full_name, message)
        )
        await db.commit()
        return cursor.lastrowid

async def get_user_appeals(user_id: int) -> List[Dict]:
    """Получение всех обращений пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals WHERE user_id = ? ORDER BY created_at DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_appeal(appeal_id: int) -> Optional[Dict]:
    """Получение конкретного обращения"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals WHERE id = ?""",
            (appeal_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_appeal_status(appeal_id: int, status: str):
    """Обновление статуса обращения"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """UPDATE appeals SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, appeal_id)
        )
        await db.commit()

async def add_admin_response(appeal_id: int, response: str):
    """Добавление ответа администратора"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """UPDATE appeals SET response = ?, status = 'closed',
               admin_response_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (response, appeal_id)
        )
        await db.commit()

async def get_new_appeals() -> List[Dict]:
    """Получение новых обращений"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals WHERE status = 'new' ORDER BY created_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

"""Работа с базой данных обращений"""
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional
import config


class Database:
    """Класс для работы с базой данных"""

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    appeal_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'new'
                )
            ''')
            await db.commit()

    async def add_appeal(self, user_id: int, username: Optional[str],
                        full_name: str, appeal_text: str) -> int:
        """Добавление нового обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                '''INSERT INTO appeals (user_id, username, full_name, appeal_text)
                   VALUES (?, ?, ?, ?)''',
                (user_id, username, full_name, appeal_text)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_all_appeals(self) -> List[Dict]:
        """Получение всех обращений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM appeals ORDER BY created_at DESC'
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_appeal(self, appeal_id: int) -> Optional[Dict]:
        """Получение обращения по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM appeals WHERE id = ?', (appeal_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_status(self, appeal_id: int, status: str):
        """Обновление статуса обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE appeals SET status = ? WHERE id = ?',
                (status, appeal_id)
            )
            await db.commit()

    async def get_stats(self) -> Dict:
        """Получение статистики"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT COUNT(*) FROM appeals') as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM appeals WHERE status = 'new'"
            ) as cursor:
                new = (await cursor.fetchone())[0]

            return {'total': total, 'new': new, 'processed': total - new}

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

async def get_appeals_by_status(status: str, limit: int = 10, offset: int = 0) -> List[Dict]:
    """Получение обращений по статусу с пагинацией"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals WHERE status = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (status, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_all_appeals(limit: int = 10, offset: int = 0) -> List[Dict]:
    """Получение всех обращений с пагинацией"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def count_appeals_by_status(status: str) -> int:
    """Подсчёт обращений по статусу"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT COUNT(*) FROM appeals WHERE status = ?""",
            (status,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def count_all_appeals() -> int:
    """Подсчёт всех обращений"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """SELECT COUNT(*) FROM appeals"""
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_statistics() -> Dict:
    """Получение статистики по обращениям"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        stats = {}

        # Общее количество
        async with db.execute("SELECT COUNT(*) FROM appeals") as cursor:
            row = await cursor.fetchone()
            stats['total'] = row[0] if row else 0

        # По статусам
        for status in ['new', 'in_progress', 'closed']:
            async with db.execute(
                "SELECT COUNT(*) FROM appeals WHERE status = ?", (status,)
            ) as cursor:
                row = await cursor.fetchone()
                stats[status] = row[0] if row else 0

        # За сегодня
        async with db.execute(
            """SELECT COUNT(*) FROM appeals
               WHERE date(created_at) = date('now')"""
        ) as cursor:
            row = await cursor.fetchone()
            stats['today'] = row[0] if row else 0

        # За неделю
        async with db.execute(
            """SELECT COUNT(*) FROM appeals
               WHERE date(created_at) >= date('now', '-7 days')"""
        ) as cursor:
            row = await cursor.fetchone()
            stats['week'] = row[0] if row else 0

        # За месяц
        async with db.execute(
            """SELECT COUNT(*) FROM appeals
               WHERE date(created_at) >= date('now', '-30 days')"""
        ) as cursor:
            row = await cursor.fetchone()
            stats['month'] = row[0] if row else 0

        return stats

async def search_appeals(query: str) -> List[Dict]:
    """Поиск обращений по тексту, имени или username"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        search_pattern = f"%{query}%"
        async with db.execute(
            """SELECT * FROM appeals
               WHERE message LIKE ? OR full_name LIKE ? OR username LIKE ?
               ORDER BY created_at DESC LIMIT 20""",
            (search_pattern, search_pattern, search_pattern)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def export_appeals_to_text() -> str:
    """Экспорт всех обращений в текстовый формат"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM appeals ORDER BY created_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()

            text = "ЭКСПОРТ ОБРАЩЕНИЙ\n"
            text += "=" * 80 + "\n\n"

            for row in rows:
                appeal = dict(row)
                text += f"ID: {appeal['id']}\n"
                text += f"От: {appeal['full_name']} (@{appeal['username']})\n"
                text += f"User ID: {appeal['user_id']}\n"
                text += f"Дата: {appeal['created_at']}\n"
                text += f"Статус: {appeal['status']}\n"
                text += f"Сообщение: {appeal['message']}\n"
                if appeal['response']:
                    text += f"Ответ: {appeal['response']}\n"
                    text += f"Дата ответа: {appeal['admin_response_at']}\n"
                text += "-" * 80 + "\n\n"

            return text

# Функции удаления обращений

async def delete_appeal(appeal_id: int) -> bool:
    """Удаление конкретного обращения по ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """DELETE FROM appeals WHERE id = ?""",
            (appeal_id,)
        )
        await db.commit()
        return cursor.rowcount > 0

async def delete_closed_appeals() -> int:
    """Удаление всех закрытых обращений"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """DELETE FROM appeals WHERE status = 'closed'"""
        )
        await db.commit()
        return cursor.rowcount

async def delete_old_appeals(days: int) -> int:
    """Удаление обращений старше указанного количества дней"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """DELETE FROM appeals
               WHERE date(created_at) < date('now', ? || ' days')""",
            (f'-{days}',)
        )
        await db.commit()
        return cursor.rowcount

async def delete_all_appeals() -> int:
    """Удаление ВСЕХ обращений (осторожно!)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""DELETE FROM appeals""")
        await db.commit()
        # Сброс автоинкремента
        await db.execute("""DELETE FROM sqlite_sequence WHERE name='appeals'""")
        await db.commit()
        return cursor.rowcount

async def delete_appeals_by_status(status: str) -> int:
    """Удаление обращений по статусу"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """DELETE FROM appeals WHERE status = ?""",
            (status,)
        )
        await db.commit()
        return cursor.rowcount

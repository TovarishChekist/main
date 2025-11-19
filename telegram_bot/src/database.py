# -*- coding: utf-8 -*-
"""
Модуль работы с базой данных
Хранение заявок, обращений и статистики
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных SQLite"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Создаем директорию если её нет
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка базы данных: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Инициализация структуры базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица обращений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    media_type TEXT,
                    media_file_id TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP,
                    response_text TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Таблица заявок на вступление
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    fio TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    school TEXT NOT NULL,
                    class TEXT NOT NULL,
                    username TEXT NOT NULL,
                    motivation TEXT NOT NULL,
                    experience TEXT NOT NULL,
                    contacts TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    review_comment TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # Таблица статистики
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица блокировок пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    blocked_by INTEGER NOT NULL,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    unblocked_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (blocked_by) REFERENCES users (user_id)
                )
            """)

            # Индексы для оптимизации
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appeals_user ON appeals(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_appeals_status ON appeals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocks_user ON user_blocks(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocks_active ON user_blocks(is_active)")

            logger.info("База данных инициализирована успешно")

    # ========== ПОЛЬЗОВАТЕЛИ ==========

    def add_or_update_user(self, user_id: int, username: str = None,
                          first_name: str = None, last_name: str = None):
        """Добавить или обновить пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_active = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, last_name))

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ========== ОБРАЩЕНИЯ ==========

    def add_appeal(self, user_id: int, text: str, media_type: str = None,
                   media_file_id: str = None) -> int:
        """Добавить обращение"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appeals (user_id, text, media_type, media_file_id)
                VALUES (?, ?, ?, ?)
            """, (user_id, text, media_type, media_file_id))
            appeal_id = cursor.lastrowid
            logger.info(f"Добавлено обращение #{appeal_id} от пользователя {user_id}")
            return appeal_id

    def get_appeal(self, appeal_id: int) -> Optional[Dict]:
        """Получить обращение по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_appeal_status(self, appeal_id: int, status: str,
                            response_text: str = None):
        """Обновить статус обращения"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE appeals
                SET status = ?, response_text = ?, responded_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, response_text, appeal_id))
            logger.info(f"Обращение #{appeal_id} обновлено: {status}")

    def get_user_appeals(self, user_id: int) -> List[Dict]:
        """Получить все обращения пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM appeals
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ========== ЗАЯВКИ ==========

    def add_application(self, user_id: int, data: Dict[str, Any]) -> int:
        """Добавить заявку на вступление"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO applications
                (user_id, fio, age, school, class, username, motivation, experience, contacts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                data.get('fio'),
                data.get('age'),
                data.get('school'),
                data.get('class'),
                data.get('username'),
                data.get('motivation'),
                data.get('experience'),
                data.get('contacts')
            ))
            app_id = cursor.lastrowid
            logger.info(f"Добавлена заявка #{app_id} от пользователя {user_id}")
            return app_id

    def get_application(self, app_id: int) -> Optional[Dict]:
        """Получить заявку по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_application_status(self, app_id: int, status: str,
                                  review_comment: str = None):
        """Обновить статус заявки"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE applications
                SET status = ?, review_comment = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, review_comment, app_id))
            logger.info(f"Заявка #{app_id} обновлена: {status}")

    def get_user_applications(self, user_id: int) -> List[Dict]:
        """Получить все заявки пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM applications
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ========== СТАТИСТИКА ==========

    def log_event(self, event_type: str, event_data: str = None):
        """Записать событие в статистику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO statistics (event_type, event_data)
                VALUES (?, ?)
            """, (event_type, event_data))

    def get_statistics(self, event_type: str = None, days: int = 30) -> List[Dict]:
        """Получить статистику за период"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute("""
                    SELECT * FROM statistics
                    WHERE event_type = ?
                    AND created_at >= datetime('now', '-' || ? || ' days')
                    ORDER BY created_at DESC
                """, (event_type, days))
            else:
                cursor.execute("""
                    SELECT * FROM statistics
                    WHERE created_at >= datetime('now', '-' || ? || ' days')
                    ORDER BY created_at DESC
                """, (days,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats_summary(self) -> Dict[str, int]:
        """Получить сводную статистику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Всего пользователей
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]

            # Всего обращений
            cursor.execute("SELECT COUNT(*) FROM appeals")
            stats['total_appeals'] = cursor.fetchone()[0]

            # Новых обращений
            cursor.execute("SELECT COUNT(*) FROM appeals WHERE status = 'new'")
            stats['new_appeals'] = cursor.fetchone()[0]

            # Всего заявок
            cursor.execute("SELECT COUNT(*) FROM applications")
            stats['total_applications'] = cursor.fetchone()[0]

            # Заявок на рассмотрении
            cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
            stats['pending_applications'] = cursor.fetchone()[0]

            # Одобренных заявок
            cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'approved'")
            stats['approved_applications'] = cursor.fetchone()[0]

            return stats

    # ========== БЛОКИРОВКИ ПОЛЬЗОВАТЕЛЕЙ ==========

    def block_user(self, user_id: int, reason: str, blocked_by: int) -> int:
        """Заблокировать пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Сначала деактивируем все предыдущие блокировки
            cursor.execute("""
                UPDATE user_blocks
                SET is_active = 0, unblocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))

            # Добавляем новую блокировку
            cursor.execute("""
                INSERT INTO user_blocks (user_id, reason, blocked_by)
                VALUES (?, ?, ?)
            """, (user_id, reason, blocked_by))
            block_id = cursor.lastrowid
            logger.info(f"Пользователь {user_id} заблокирован администратором {blocked_by}. Причина: {reason}")
            return block_id

    def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_blocks
                SET is_active = 0, unblocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))

            if cursor.rowcount > 0:
                logger.info(f"Пользователь {user_id} разблокирован")
                return True
            return False

    def is_user_blocked(self, user_id: int) -> bool:
        """Проверить, заблокирован ли пользователь"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_blocks
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            return cursor.fetchone()[0] > 0

    def get_block_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о блокировке пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_blocks
                WHERE user_id = ? AND is_active = 1
                ORDER BY blocked_at DESC
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_blocked_users(self) -> List[Dict]:
        """Получить список всех заблокированных пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ub.*, u.username, u.first_name, u.last_name
                FROM user_blocks ub
                LEFT JOIN users u ON ub.user_id = u.user_id
                WHERE ub.is_active = 1
                ORDER BY ub.blocked_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_block_history(self, user_id: int) -> List[Dict]:
        """Получить историю блокировок пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_blocks
                WHERE user_id = ?
                ORDER BY blocked_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]


# Глобальный экземпляр базы данных (будет инициализирован в config)
db: Optional[Database] = None

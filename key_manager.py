"""
Модуль управления ключами шифрования
Безопасное хранение и управление ключами пользователей
"""
import sqlite3
import json
import os
from typing import Optional, Dict, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
import base64


class KeyManager:
    """Управление ключами шифрования пользователей"""

    def __init__(self, db_path: str = "keys.db", master_key: Optional[bytes] = None):
        """
        Инициализация менеджера ключей
        master_key - главный ключ для шифрования приватных ключей в БД
        """
        self.db_path = db_path

        # Генерация или загрузка мастер-ключа
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._load_or_create_master_key()

        self.fernet = Fernet(self.master_key)
        self._init_database()

    def _load_or_create_master_key(self) -> bytes:
        """Загрузка или создание мастер-ключа"""
        key_file = '.master_key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Только владелец может читать
            return key

    def _init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей с их ключами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                private_key_encrypted BLOB,
                public_key TEXT,
                symmetric_key_encrypted BLOB,
                created_at TEXT,
                last_used TEXT
            )
        ''')

        # Таблица общих ключей для переписки между пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                shared_key_encrypted BLOB,
                created_at TEXT,
                UNIQUE(user1_id, user2_id)
            )
        ''')

        # Таблица сохраненных паролей для симметричного шифрования
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_passwords (
                user_id INTEGER,
                password_name TEXT,
                password_hash TEXT,
                salt BLOB,
                created_at TEXT,
                PRIMARY KEY (user_id, password_name)
            )
        ''')

        conn.commit()
        conn.close()

    # ============= УПРАВЛЕНИЕ КЛЮЧАМИ ПОЛЬЗОВАТЕЛЕЙ =============

    def create_user_keys(self, user_id: int, username: str,
                         private_key: bytes, public_key: bytes,
                         symmetric_key: bytes) -> bool:
        """
        Создание и сохранение ключей для нового пользователя
        Приватные ключи шифруются перед сохранением
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Шифрование приватного ключа и симметричного ключа
            encrypted_private = self.fernet.encrypt(private_key)
            encrypted_symmetric = self.fernet.encrypt(symmetric_key)

            cursor.execute('''
                INSERT OR REPLACE INTO user_keys
                (user_id, username, private_key_encrypted, public_key,
                 symmetric_key_encrypted, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                username,
                encrypted_private,
                public_key.decode('utf-8'),
                encrypted_symmetric,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка создания ключей: {e}")
            return False

    def get_user_keys(self, user_id: int) -> Optional[Dict]:
        """Получение ключей пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT private_key_encrypted, public_key, symmetric_key_encrypted
                FROM user_keys WHERE user_id = ?
            ''', (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                encrypted_private, public_key, encrypted_symmetric = result

                # Расшифровка приватных данных
                private_key = self.fernet.decrypt(encrypted_private)
                symmetric_key = self.fernet.decrypt(encrypted_symmetric)

                return {
                    'private_key': private_key,
                    'public_key': public_key.encode('utf-8'),
                    'symmetric_key': symmetric_key
                }
            return None
        except Exception as e:
            print(f"Ошибка получения ключей: {e}")
            return None

    def get_public_key(self, user_id: int) -> Optional[bytes]:
        """Получение только публичного ключа пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT public_key FROM user_keys WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0].encode('utf-8')
            return None
        except Exception as e:
            print(f"Ошибка получения публичного ключа: {e}")
            return None

    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM user_keys WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def update_last_used(self, user_id: int):
        """Обновление времени последнего использования"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_keys SET last_used = ? WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

    def delete_user_keys(self, user_id: int) -> bool:
        """Удаление всех ключей пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM user_keys WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM shared_keys WHERE user1_id = ? OR user2_id = ?',
                          (user_id, user_id))
            cursor.execute('DELETE FROM saved_passwords WHERE user_id = ?', (user_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления ключей: {e}")
            return False

    # ============= УПРАВЛЕНИЕ ОБЩИМИ КЛЮЧАМИ =============

    def create_shared_key(self, user1_id: int, user2_id: int, shared_key: bytes) -> bool:
        """Создание общего ключа для переписки между двумя пользователями"""
        try:
            # Сортируем ID, чтобы избежать дубликатов
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            encrypted_key = self.fernet.encrypt(shared_key)

            cursor.execute('''
                INSERT OR REPLACE INTO shared_keys
                (user1_id, user2_id, shared_key_encrypted, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user1_id, user2_id, encrypted_key, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка создания общего ключа: {e}")
            return False

    def get_shared_key(self, user1_id: int, user2_id: int) -> Optional[bytes]:
        """Получение общего ключа для переписки"""
        try:
            # Сортируем ID
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT shared_key_encrypted FROM shared_keys
                WHERE user1_id = ? AND user2_id = ?
            ''', (user1_id, user2_id))

            result = cursor.fetchone()
            conn.close()

            if result:
                return self.fernet.decrypt(result[0])
            return None
        except Exception as e:
            print(f"Ошибка получения общего ключа: {e}")
            return None

    # ============= УПРАВЛЕНИЕ ПАРОЛЯМИ =============

    def save_password_info(self, user_id: int, password_name: str,
                           password_hash: str, salt: bytes) -> bool:
        """Сохранение информации о пароле для симметричного шифрования"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO saved_passwords
                (user_id, password_name, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, password_name, password_hash, salt, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка сохранения пароля: {e}")
            return False

    def get_password_info(self, user_id: int, password_name: str) -> Optional[Tuple[str, bytes]]:
        """Получение информации о сохраненном пароле"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT password_hash, salt FROM saved_passwords
                WHERE user_id = ? AND password_name = ?
            ''', (user_id, password_name))

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0], result[1]
            return None
        except Exception as e:
            print(f"Ошибка получения пароля: {e}")
            return None

    def list_saved_passwords(self, user_id: int) -> list:
        """Список сохраненных паролей пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT password_name, created_at FROM saved_passwords
                WHERE user_id = ?
            ''', (user_id,))

            results = cursor.fetchall()
            conn.close()

            return [{'name': name, 'created': created} for name, created in results]
        except Exception as e:
            print(f"Ошибка получения списка паролей: {e}")
            return []

    # ============= СТАТИСТИКА =============

    def get_statistics(self, user_id: int) -> Dict:
        """Получение статистики использования"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Информация о пользователе
            cursor.execute('''
                SELECT created_at, last_used FROM user_keys WHERE user_id = ?
            ''', (user_id,))
            user_info = cursor.fetchone()

            # Количество общих ключей
            cursor.execute('''
                SELECT COUNT(*) FROM shared_keys
                WHERE user1_id = ? OR user2_id = ?
            ''', (user_id, user_id))
            shared_count = cursor.fetchone()[0]

            # Количество сохраненных паролей
            cursor.execute('''
                SELECT COUNT(*) FROM saved_passwords WHERE user_id = ?
            ''', (user_id,))
            passwords_count = cursor.fetchone()[0]

            conn.close()

            if user_info:
                return {
                    'registered': user_info[0],
                    'last_used': user_info[1],
                    'shared_keys_count': shared_count,
                    'saved_passwords_count': passwords_count
                }
            return {}
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {}

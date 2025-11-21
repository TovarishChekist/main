"""
Модуль для шифрования и дешифрования файлов
Поддерживает файлы любого размера с потоковой обработкой
"""
import os
from typing import Tuple, BinaryIO
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypto_manager import CryptoManager


class FileCryptoManager:
    """Управление шифрованием файлов"""

    def __init__(self):
        self.crypto = CryptoManager()
        self.chunk_size = 64 * 1024  # 64KB chunks для потоковой обработки

    def encrypt_file(self, input_path: str, output_path: str, key: bytes) -> Tuple[bytes, str]:
        """
        Шифрование файла с AES-256-GCM
        Использует потоковую обработку для больших файлов

        Возвращает (nonce, output_path)
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)

        # Получаем размер файла
        file_size = os.path.getsize(input_path)

        with open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                # Записываем nonce в начало файла
                f_out.write(nonce)

                # Записываем размер оригинального файла (8 байт)
                f_out.write(file_size.to_bytes(8, byteorder='big'))

                # Читаем и шифруем файл по частям
                while True:
                    chunk = f_in.read(self.chunk_size)
                    if not chunk:
                        break

                    # Шифруем chunk
                    encrypted_chunk = aesgcm.encrypt(nonce, chunk, None)

                    # Записываем размер зашифрованного chunk (4 байта) + chunk
                    chunk_size = len(encrypted_chunk)
                    f_out.write(chunk_size.to_bytes(4, byteorder='big'))
                    f_out.write(encrypted_chunk)

        return nonce, output_path

    def decrypt_file(self, input_path: str, output_path: str, key: bytes) -> str:
        """
        Дешифрование файла с AES-256-GCM
        Использует потоковую обработку для больших файлов

        Возвращает output_path
        """
        aesgcm = AESGCM(key)

        with open(input_path, 'rb') as f_in:
            # Читаем nonce (12 байт)
            nonce = f_in.read(12)

            # Читаем размер оригинального файла (8 байт)
            original_size = int.from_bytes(f_in.read(8), byteorder='big')

            with open(output_path, 'wb') as f_out:
                total_written = 0

                # Читаем и дешифруем файл по частям
                while True:
                    # Читаем размер chunk
                    chunk_size_bytes = f_in.read(4)
                    if not chunk_size_bytes:
                        break

                    chunk_size = int.from_bytes(chunk_size_bytes, byteorder='big')

                    # Читаем зашифрованный chunk
                    encrypted_chunk = f_in.read(chunk_size)
                    if not encrypted_chunk:
                        break

                    # Дешифруем chunk
                    decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk, None)

                    # Записываем расшифрованные данные
                    bytes_to_write = min(len(decrypted_chunk), original_size - total_written)
                    f_out.write(decrypted_chunk[:bytes_to_write])
                    total_written += bytes_to_write

        return output_path

    def encrypt_file_with_password(self, input_path: str, output_path: str,
                                   password: str) -> Tuple[bytes, bytes]:
        """
        Шифрование файла с паролем
        Возвращает (salt, nonce)
        """
        # Деривация ключа из пароля
        key, salt = self.crypto.derive_key_from_password(password)

        # Шифрование файла
        nonce, _ = self.encrypt_file(input_path, output_path, key)

        return salt, nonce

    def decrypt_file_with_password(self, input_path: str, output_path: str,
                                   password: str, salt: bytes) -> str:
        """
        Дешифрование файла с паролем
        Возвращает output_path
        """
        # Деривация ключа из пароля
        key, _ = self.crypto.derive_key_from_password(password, salt)

        # Дешифрование файла
        return self.decrypt_file(input_path, output_path, key)

    def get_encrypted_file_info(self, file_path: str) -> dict:
        """Получение информации о зашифрованном файле"""
        try:
            file_size = os.path.getsize(file_path)

            with open(file_path, 'rb') as f:
                # Пропускаем nonce (12 байт)
                f.seek(12)
                # Читаем размер оригинального файла
                original_size = int.from_bytes(f.read(8), byteorder='big')

            return {
                'encrypted_size': file_size,
                'original_size': original_size,
                'overhead': file_size - original_size
            }
        except Exception as e:
            return {'error': str(e)}

"""
Модуль криптографии для бота-шифровальщика
Реализует AES-256-GCM, RSA-4096, ChaCha20-Poly1305
"""
import os
import base64
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoManager:
    """Управление всеми криптографическими операциями"""

    def __init__(self):
        self.backend = default_backend()

    # ============= СИММЕТРИЧНОЕ ШИФРОВАНИЕ (AES-256-GCM) =============

    def generate_symmetric_key(self) -> bytes:
        """Генерация случайного 256-битного ключа для AES"""
        return AESGCM.generate_key(bit_length=256)

    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Деривация ключа из пароля с использованием PBKDF2
        Возвращает (ключ, соль)
        """
        if salt is None:
            salt = os.urandom(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # Высокое число итераций для безопасности
            backend=self.backend
        )
        key = kdf.derive(password.encode())
        return key, salt

    def encrypt_aes_gcm(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Шифрование с AES-256-GCM (обеспечивает конфиденциальность и аутентичность)
        Возвращает (ciphertext, nonce)
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-битный nonce для GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce

    def decrypt_aes_gcm(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Дешифрование с AES-256-GCM"""
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext

    # ============= CHACHA20-POLY1305 (альтернатива AES) =============

    def encrypt_chacha20(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Шифрование с ChaCha20-Poly1305 (быстрее AES на некоторых платформах)
        Возвращает (ciphertext, nonce)
        """
        chacha = ChaCha20Poly1305(key)
        nonce = os.urandom(12)
        ciphertext = chacha.encrypt(nonce, plaintext, None)
        return ciphertext, nonce

    def decrypt_chacha20(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Дешифрование с ChaCha20-Poly1305"""
        chacha = ChaCha20Poly1305(key)
        plaintext = chacha.decrypt(nonce, ciphertext, None)
        return plaintext

    # ============= АСИММЕТРИЧНОЕ ШИФРОВАНИЕ (RSA-4096) =============

    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """
        Генерация пары ключей RSA-4096
        Возвращает (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=self.backend
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    def encrypt_rsa(self, plaintext: bytes, public_key_pem: bytes) -> bytes:
        """
        Шифрование с использованием RSA-OAEP
        Примечание: RSA может шифровать только ограниченный объем данных
        """
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=self.backend
        )

        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt_rsa(self, ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """Дешифрование с использованием RSA-OAEP"""
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=self.backend
        )

        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext

    # ============= ГИБРИДНОЕ ШИФРОВАНИЕ (RSA + AES) =============

    def hybrid_encrypt(self, plaintext: bytes, public_key_pem: bytes) -> dict:
        """
        Гибридное шифрование: генерируется AES ключ, данные шифруются AES,
        AES ключ шифруется RSA
        """
        # Генерация случайного AES ключа
        aes_key = self.generate_symmetric_key()

        # Шифрование данных с AES
        ciphertext, nonce = self.encrypt_aes_gcm(plaintext, aes_key)

        # Шифрование AES ключа с RSA
        encrypted_key = self.encrypt_rsa(aes_key, public_key_pem)

        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'nonce': base64.b64encode(nonce).decode(),
            'encrypted_key': base64.b64encode(encrypted_key).decode()
        }

    def hybrid_decrypt(self, encrypted_data: dict, private_key_pem: bytes) -> bytes:
        """Дешифрование гибридно зашифрованных данных"""
        # Декодирование из base64
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])

        # Расшифровка AES ключа с помощью RSA
        aes_key = self.decrypt_rsa(encrypted_key, private_key_pem)

        # Расшифровка данных с помощью AES
        plaintext = self.decrypt_aes_gcm(ciphertext, aes_key, nonce)

        return plaintext

    # ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

    def hash_data(self, data: bytes, algorithm: str = 'sha256') -> str:
        """Хеширование данных (SHA-256, SHA-512, SHA3-256)"""
        if algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data).hexdigest()
        elif algorithm == 'sha3-256':
            return hashlib.sha3_256(data).hexdigest()
        else:
            raise ValueError(f"Неподдерживаемый алгоритм: {algorithm}")

    def encode_for_telegram(self, data: bytes) -> str:
        """Кодирование двоичных данных в base64 для передачи через Telegram"""
        return base64.b64encode(data).decode('utf-8')

    def decode_from_telegram(self, encoded: str) -> bytes:
        """Декодирование данных из base64"""
        return base64.b64decode(encoded.encode('utf-8'))

    def secure_compare(self, a: bytes, b: bytes) -> bool:
        """Безопасное сравнение байтов (защита от timing attacks)"""
        return hashlib.compare_digest(a, b)

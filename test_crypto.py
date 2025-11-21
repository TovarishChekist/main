"""
Тесты безопасности для криптографических функций
"""
import os
import tempfile
from crypto_manager import CryptoManager
from key_manager import KeyManager
from file_crypto import FileCryptoManager


def test_aes_encryption():
    """Тест AES-256-GCM шифрования"""
    print("🔐 Тест AES-256-GCM...")

    crypto = CryptoManager()

    # Генерация ключа
    key = crypto.generate_symmetric_key()
    assert len(key) == 32, "Ключ должен быть 256 бит (32 байта)"

    # Шифрование
    plaintext = b"Secret message for testing AES-256-GCM encryption!"
    ciphertext, nonce = crypto.encrypt_aes_gcm(plaintext, key)

    assert len(nonce) == 12, "Nonce должен быть 96 бит (12 байт)"
    assert ciphertext != plaintext, "Зашифрованный текст должен отличаться от исходного"

    # Расшифровка
    decrypted = crypto.decrypt_aes_gcm(ciphertext, key, nonce)
    assert decrypted == plaintext, "Расшифрованный текст должен совпадать с исходным"

    print("✅ AES-256-GCM: OK")


def test_chacha20_encryption():
    """Тест ChaCha20-Poly1305 шифрования"""
    print("🚀 Тест ChaCha20-Poly1305...")

    crypto = CryptoManager()

    # Генерация ключа
    key = crypto.generate_symmetric_key()

    # Шифрование
    plaintext = b"Testing ChaCha20-Poly1305 encryption algorithm!"
    ciphertext, nonce = crypto.encrypt_chacha20(plaintext, key)

    assert ciphertext != plaintext, "Зашифрованный текст должен отличаться"

    # Расшифровка
    decrypted = crypto.decrypt_chacha20(ciphertext, key, nonce)
    assert decrypted == plaintext, "Расшифрованный текст должен совпадать"

    print("✅ ChaCha20-Poly1305: OK")


def test_rsa_encryption():
    """Тест RSA-4096 шифрования"""
    print("🔑 Тест RSA-4096...")

    crypto = CryptoManager()

    # Генерация ключей
    private_key, public_key = crypto.generate_rsa_keypair()

    # Проверка формата ключей
    assert b'BEGIN PRIVATE KEY' in private_key, "Неверный формат приватного ключа"
    assert b'BEGIN PUBLIC KEY' in public_key, "Неверный формат публичного ключа"

    # Шифрование
    plaintext = b"RSA test message"
    ciphertext = crypto.encrypt_rsa(plaintext, public_key)

    assert ciphertext != plaintext, "Зашифрованный текст должен отличаться"

    # Расшифровка
    decrypted = crypto.decrypt_rsa(ciphertext, private_key)
    assert decrypted == plaintext, "Расшифрованный текст должен совпадать"

    print("✅ RSA-4096: OK")


def test_hybrid_encryption():
    """Тест гибридного шифрования"""
    print("⚡ Тест гибридного шифрования...")

    crypto = CryptoManager()

    # Генерация ключей
    private_key, public_key = crypto.generate_rsa_keypair()

    # Шифрование большого текста
    plaintext = b"A" * 10000  # 10KB данных
    encrypted_data = crypto.hybrid_encrypt(plaintext, public_key)

    # Проверка структуры
    assert 'ciphertext' in encrypted_data, "Отсутствует ciphertext"
    assert 'nonce' in encrypted_data, "Отсутствует nonce"
    assert 'encrypted_key' in encrypted_data, "Отсутствует encrypted_key"

    # Расшифровка
    decrypted = crypto.hybrid_decrypt(encrypted_data, private_key)
    assert decrypted == plaintext, "Расшифрованный текст должен совпадать"

    print("✅ Гибридное шифрование: OK")


def test_password_derivation():
    """Тест деривации ключа из пароля"""
    print("🔐 Тест PBKDF2 деривации...")

    crypto = CryptoManager()

    password = "SuperSecretPassword123!"

    # Деривация с одинаковым salt должна давать одинаковый ключ
    key1, salt = crypto.derive_key_from_password(password)
    key2, _ = crypto.derive_key_from_password(password, salt)

    assert key1 == key2, "Ключи с одинаковым паролем и salt должны совпадать"
    assert len(key1) == 32, "Ключ должен быть 256 бит"
    assert len(salt) == 32, "Salt должен быть 256 бит"

    # Разные salt должны давать разные ключи
    key3, salt3 = crypto.derive_key_from_password(password)
    assert key1 != key3, "Ключи с разными salt должны отличаться"

    print("✅ PBKDF2: OK")


def test_key_manager():
    """Тест управления ключами"""
    print("🗝️ Тест KeyManager...")

    # Используем временную БД
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name

    try:
        key_manager = KeyManager(db_path=db_path)
        crypto = CryptoManager()

        # Создание ключей пользователя
        user_id = 12345
        username = "testuser"

        private_key, public_key = crypto.generate_rsa_keypair()
        symmetric_key = crypto.generate_symmetric_key()

        success = key_manager.create_user_keys(
            user_id, username, private_key, public_key, symmetric_key
        )
        assert success, "Создание ключей должно быть успешным"

        # Проверка существования
        assert key_manager.user_exists(user_id), "Пользователь должен существовать"

        # Получение ключей
        keys = key_manager.get_user_keys(user_id)
        assert keys is not None, "Ключи должны быть получены"
        assert keys['private_key'] == private_key, "Приватный ключ должен совпадать"
        assert keys['public_key'] == public_key, "Публичный ключ должен совпадать"

        # Удаление ключей
        success = key_manager.delete_user_keys(user_id)
        assert success, "Удаление ключей должно быть успешным"
        assert not key_manager.user_exists(user_id), "Пользователь не должен существовать"

        print("✅ KeyManager: OK")

    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_file_encryption():
    """Тест шифрования файлов"""
    print("📁 Тест шифрования файлов...")

    file_crypto = FileCryptoManager()
    crypto = CryptoManager()

    # Создаем временный файл с данными
    with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp_in:
        test_data = b"File encryption test data " * 1000  # ~25KB
        tmp_in.write(test_data)
        input_path = tmp_in.name

    with tempfile.NamedTemporaryFile(delete=False) as tmp_enc:
        encrypted_path = tmp_enc.name

    with tempfile.NamedTemporaryFile(delete=False) as tmp_dec:
        decrypted_path = tmp_dec.name

    try:
        # Шифрование файла с паролем
        password = "FileEncryptionPassword123"
        salt, nonce = file_crypto.encrypt_file_with_password(
            input_path, encrypted_path, password
        )

        assert os.path.exists(encrypted_path), "Зашифрованный файл должен существовать"

        # Получение информации о зашифрованном файле
        file_info = file_crypto.get_encrypted_file_info(encrypted_path)
        assert 'original_size' in file_info, "Должен быть размер оригинального файла"

        # Расшифровка файла
        file_crypto.decrypt_file_with_password(
            encrypted_path, decrypted_path, password, salt
        )

        assert os.path.exists(decrypted_path), "Расшифрованный файл должен существовать"

        # Проверка содержимого
        with open(decrypted_path, 'rb') as f:
            decrypted_data = f.read()

        assert decrypted_data == test_data, "Расшифрованные данные должны совпадать"

        print("✅ Шифрование файлов: OK")

    finally:
        # Очистка
        for path in [input_path, encrypted_path, decrypted_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_hash_functions():
    """Тест функций хеширования"""
    print("🔐 Тест хеширования...")

    crypto = CryptoManager()

    data = b"Test data for hashing"

    # SHA-256
    hash_256 = crypto.hash_data(data, 'sha256')
    assert len(hash_256) == 64, "SHA-256 хеш должен быть 64 символа (256 бит)"

    # SHA-512
    hash_512 = crypto.hash_data(data, 'sha512')
    assert len(hash_512) == 128, "SHA-512 хеш должен быть 128 символов (512 бит)"

    # SHA3-256
    hash_sha3 = crypto.hash_data(data, 'sha3-256')
    assert len(hash_sha3) == 64, "SHA3-256 хеш должен быть 64 символа"

    # Одинаковые данные должны давать одинаковый хеш
    hash_256_2 = crypto.hash_data(data, 'sha256')
    assert hash_256 == hash_256_2, "Хеши одинаковых данных должны совпадать"

    # Разные данные должны давать разные хеши
    hash_different = crypto.hash_data(b"Different data", 'sha256')
    assert hash_256 != hash_different, "Хеши разных данных должны отличаться"

    print("✅ Хеширование: OK")


def test_security_properties():
    """Тест свойств безопасности"""
    print("🛡️ Тест свойств безопасности...")

    crypto = CryptoManager()

    # 1. Одинаковый plaintext с разными nonce должен давать разные ciphertext
    key = crypto.generate_symmetric_key()
    plaintext = b"Same message"

    ciphertext1, nonce1 = crypto.encrypt_aes_gcm(plaintext, key)
    ciphertext2, nonce2 = crypto.encrypt_aes_gcm(plaintext, key)

    assert nonce1 != nonce2, "Nonce должны быть разными"
    assert ciphertext1 != ciphertext2, "Ciphertext должны быть разными"

    # 2. Невозможность расшифровки без правильного ключа
    wrong_key = crypto.generate_symmetric_key()

    try:
        crypto.decrypt_aes_gcm(ciphertext1, wrong_key, nonce1)
        assert False, "Расшифровка с неверным ключом должна провалиться"
    except Exception:
        pass  # Ожидаемое поведение

    # 3. Secure compare
    data1 = b"test"
    data2 = b"test"
    data3 = b"different"

    assert crypto.secure_compare(data1, data2), "Одинаковые данные должны совпадать"
    assert not crypto.secure_compare(data1, data3), "Разные данные не должны совпадать"

    print("✅ Свойства безопасности: OK")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("🧪 ЗАПУСК ТЕСТОВ БЕЗОПАСНОСТИ")
    print("="*60 + "\n")

    tests = [
        test_aes_encryption,
        test_chacha20_encryption,
        test_rsa_encryption,
        test_hybrid_encryption,
        test_password_derivation,
        test_key_manager,
        test_file_encryption,
        test_hash_functions,
        test_security_properties,
    ]

    failed = 0

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ ПРОВАЛ: {test.__name__}")
            print(f"   Ошибка: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ОШИБКА: {test.__name__}")
            print(f"   Исключение: {e}")
            failed += 1

    print("\n" + "="*60)
    if failed == 0:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print(f"⚠️ ПРОВАЛЕНО ТЕСТОВ: {failed}/{len(tests)}")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()

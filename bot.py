"""
Продвинутый Telegram бот-шифровальщик
Поддерживает множественные режимы шифрования и E2E коммуникацию
"""
import asyncio
import os
import json
import tempfile
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from crypto_manager import CryptoManager
from key_manager import KeyManager
from file_crypto import FileCryptoManager


# ============= СОСТОЯНИЯ FSM =============

class EncryptionStates(StatesGroup):
    """Состояния для процесса шифрования"""
    waiting_for_text = State()
    waiting_for_password = State()
    waiting_for_decryption_text = State()
    waiting_for_decryption_password = State()
    waiting_for_recipient_id = State()
    waiting_for_e2e_message = State()
    # Файлы
    waiting_for_file_to_encrypt = State()
    waiting_for_file_password = State()
    waiting_for_file_to_decrypt = State()
    waiting_for_decrypt_file_password = State()


# ============= КОНФИГУРАЦИЯ =============

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
crypto = CryptoManager()
key_manager = KeyManager()
file_crypto = FileCryptoManager()


# ============= КЛАВИАТУРЫ =============

def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔐 Зашифровать текст", callback_data="encrypt_text"),
            InlineKeyboardButton(text="🔓 Расшифровать текст", callback_data="decrypt_text")
        ],
        [
            InlineKeyboardButton(text="📁 Зашифровать файл", callback_data="encrypt_file"),
            InlineKeyboardButton(text="📂 Расшифровать файл", callback_data="decrypt_file")
        ],
        [
            InlineKeyboardButton(text="🔑 Мои ключи", callback_data="my_keys"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")
        ],
        [
            InlineKeyboardButton(text="💬 E2E переписка", callback_data="e2e_chat"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_encryption_mode_menu() -> InlineKeyboardMarkup:
    """Меню выбора режима шифрования"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔐 AES-256-GCM (пароль)", callback_data="mode_aes"),
        ],
        [
            InlineKeyboardButton(text="🚀 ChaCha20-Poly1305 (пароль)", callback_data="mode_chacha"),
        ],
        [
            InlineKeyboardButton(text="🔑 RSA-4096 (мой ключ)", callback_data="mode_rsa"),
        ],
        [
            InlineKeyboardButton(text="⚡ Гибридное (RSA+AES)", callback_data="mode_hybrid"),
        ],
        [
            InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")]
    ])


# ============= ИНИЦИАЛИЗАЦИЯ БОТА =============

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ============= ОБРАБОТЧИКИ КОМАНД =============

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Проверяем, есть ли у пользователя ключи
    if not key_manager.user_exists(user_id):
        await message.answer(
            "🔐 <b>Добро пожаловать в продвинутый бот-шифровальщик!</b>\n\n"
            "Генерирую ваши ключи шифрования...",
            parse_mode="HTML"
        )

        # Генерация ключей для нового пользователя
        private_key, public_key = crypto.generate_rsa_keypair()
        symmetric_key = crypto.generate_symmetric_key()

        # Сохранение ключей
        key_manager.create_user_keys(user_id, username, private_key, public_key, symmetric_key)

        await message.answer(
            "✅ <b>Ключи успешно созданы!</b>\n\n"
            "Теперь вы можете:\n"
            "• Шифровать и расшифровывать текст и файлы\n"
            "• Использовать разные режимы шифрования\n"
            "• Безопасно общаться с другими пользователями (E2E)\n\n"
            "<b>Ваши ключи:</b>\n"
            f"🔑 RSA-4096: Создан\n"
            f"🔐 AES-256: Создан\n\n"
            "Выберите действие из меню:",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            f"👋 С возвращением, {username}!\n\n"
            "Выберите действие из меню:",
            reply_markup=get_main_menu()
        )


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Показать главное меню"""
    await message.answer(
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@dp.message(Command("keys"))
async def cmd_keys(message: types.Message):
    """Показать информацию о ключах"""
    user_id = message.from_user.id

    if not key_manager.user_exists(user_id):
        await message.answer("❌ У вас еще нет ключей. Используйте /start для создания.")
        return

    keys = key_manager.get_user_keys(user_id)
    public_key = keys['public_key'].decode('utf-8')

    # Показываем только первые и последние 50 символов публичного ключа
    key_preview = public_key[:50] + "\n...\n" + public_key[-50:]

    await message.answer(
        f"🔑 <b>Ваши ключи шифрования</b>\n\n"
        f"<b>Публичный ключ RSA-4096:</b>\n"
        f"<code>{key_preview}</code>\n\n"
        f"⚠️ Никогда не делитесь приватным ключом!",
        parse_mode="HTML",
        reply_markup=get_back_button()
    )


# ============= ОБРАБОТЧИКИ CALLBACK =============

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "encrypt_text")
async def encrypt_text_menu(callback: types.CallbackQuery):
    """Меню шифрования текста"""
    await callback.message.edit_text(
        "🔐 <b>Шифрование текста</b>\n\n"
        "Выберите режим шифрования:",
        parse_mode="HTML",
        reply_markup=get_encryption_mode_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "mode_aes")
async def mode_aes(callback: types.CallbackQuery, state: FSMContext):
    """Режим AES-256-GCM"""
    await state.update_data(mode="aes")
    await callback.message.edit_text(
        "🔐 <b>Режим: AES-256-GCM</b>\n\n"
        "Отправьте текст, который нужно зашифровать:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_text)
    await callback.answer()


@dp.callback_query(F.data == "mode_chacha")
async def mode_chacha(callback: types.CallbackQuery, state: FSMContext):
    """Режим ChaCha20-Poly1305"""
    await state.update_data(mode="chacha")
    await callback.message.edit_text(
        "🚀 <b>Режим: ChaCha20-Poly1305</b>\n\n"
        "Отправьте текст, который нужно зашифровать:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_text)
    await callback.answer()


@dp.callback_query(F.data == "mode_rsa")
async def mode_rsa(callback: types.CallbackQuery, state: FSMContext):
    """Режим RSA-4096"""
    user_id = callback.from_user.id

    if not key_manager.user_exists(user_id):
        await callback.answer("❌ Сначала создайте ключи (/start)", show_alert=True)
        return

    await state.update_data(mode="rsa")
    await callback.message.edit_text(
        "🔑 <b>Режим: RSA-4096</b>\n\n"
        "Отправьте текст для шифрования (макс. 470 байт):",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_text)
    await callback.answer()


@dp.callback_query(F.data == "mode_hybrid")
async def mode_hybrid(callback: types.CallbackQuery, state: FSMContext):
    """Режим гибридного шифрования"""
    user_id = callback.from_user.id

    if not key_manager.user_exists(user_id):
        await callback.answer("❌ Сначала создайте ключи (/start)", show_alert=True)
        return

    await state.update_data(mode="hybrid")
    await callback.message.edit_text(
        "⚡ <b>Режим: Гибридное шифрование (RSA+AES)</b>\n\n"
        "Отправьте текст любого размера для шифрования:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_text)
    await callback.answer()


@dp.message(EncryptionStates.waiting_for_text)
async def process_text_for_encryption(message: types.Message, state: FSMContext):
    """Обработка текста для шифрования"""
    data = await state.get_data()
    mode = data.get('mode')
    text = message.text

    user_id = message.from_user.id
    keys = key_manager.get_user_keys(user_id)

    try:
        if mode == "aes":
            # Запрашиваем пароль
            await state.update_data(plaintext=text)
            await message.answer(
                "🔑 Отправьте пароль для шифрования:\n\n"
                "⚠️ <b>Запомните пароль!</b> Без него расшифровать будет невозможно.",
                parse_mode="HTML"
            )
            await state.set_state(EncryptionStates.waiting_for_password)

        elif mode == "chacha":
            # Запрашиваем пароль
            await state.update_data(plaintext=text)
            await message.answer(
                "🔑 Отправьте пароль для шифрования:\n\n"
                "⚠️ <b>Запомните пароль!</b> Без него расшифровать будет невозможно.",
                parse_mode="HTML"
            )
            await state.set_state(EncryptionStates.waiting_for_password)

        elif mode == "rsa":
            # Проверка размера
            if len(text.encode()) > 470:
                await message.answer(
                    "❌ Текст слишком большой для RSA!\n"
                    "Используйте гибридное шифрование для больших текстов.",
                    reply_markup=get_back_button()
                )
                return

            # Шифрование с RSA
            ciphertext = crypto.encrypt_rsa(text.encode(), keys['public_key'])
            encoded = crypto.encode_for_telegram(ciphertext)

            await message.answer(
                "✅ <b>Текст зашифрован (RSA-4096)</b>\n\n"
                f"<code>{encoded}</code>\n\n"
                "Скопируйте зашифрованный текст для отправки.",
                parse_mode="HTML",
                reply_markup=get_back_button()
            )
            await state.clear()

        elif mode == "hybrid":
            # Гибридное шифрование
            encrypted_data = crypto.hybrid_encrypt(text.encode(), keys['public_key'])

            # Форматируем результат в JSON
            result = json.dumps(encrypted_data, indent=2)

            await message.answer(
                "✅ <b>Текст зашифрован (Гибридное RSA+AES)</b>\n\n"
                f"<code>{result}</code>\n\n"
                "Скопируйте весь JSON для расшифровки.",
                parse_mode="HTML",
                reply_markup=get_back_button()
            )
            await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Ошибка шифрования: {str(e)}",
            reply_markup=get_back_button()
        )
        await state.clear()


@dp.message(EncryptionStates.waiting_for_password)
async def process_password_for_encryption(message: types.Message, state: FSMContext):
    """Обработка пароля для шифрования"""
    data = await state.get_data()
    mode = data.get('mode')
    text = data.get('plaintext')
    password = message.text

    # Удаляем сообщение с паролем для безопасности
    await message.delete()

    try:
        # Деривация ключа из пароля
        key, salt = crypto.derive_key_from_password(password)

        if mode == "aes":
            # Шифрование с AES
            ciphertext, nonce = crypto.encrypt_aes_gcm(text.encode(), key)

            # Упаковка данных
            package = {
                'ciphertext': crypto.encode_for_telegram(ciphertext),
                'nonce': crypto.encode_for_telegram(nonce),
                'salt': crypto.encode_for_telegram(salt),
                'algorithm': 'AES-256-GCM'
            }

        elif mode == "chacha":
            # Шифрование с ChaCha20
            ciphertext, nonce = crypto.encrypt_chacha20(text.encode(), key)

            # Упаковка данных
            package = {
                'ciphertext': crypto.encode_for_telegram(ciphertext),
                'nonce': crypto.encode_for_telegram(nonce),
                'salt': crypto.encode_for_telegram(salt),
                'algorithm': 'ChaCha20-Poly1305'
            }

        result = json.dumps(package, indent=2)

        await message.answer(
            f"✅ <b>Текст зашифрован ({package['algorithm']})</b>\n\n"
            f"<code>{result}</code>\n\n"
            "Скопируйте весь JSON для расшифровки.",
            parse_mode="HTML",
            reply_markup=get_back_button()
        )

    except Exception as e:
        await message.answer(
            f"❌ Ошибка шифрования: {str(e)}",
            reply_markup=get_back_button()
        )

    await state.clear()


@dp.callback_query(F.data == "decrypt_text")
async def decrypt_text_menu(callback: types.CallbackQuery, state: FSMContext):
    """Меню расшифровки текста"""
    await callback.message.edit_text(
        "🔓 <b>Расшифровка текста</b>\n\n"
        "Отправьте зашифрованный текст (JSON или base64):",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_decryption_text)
    await callback.answer()


@dp.message(EncryptionStates.waiting_for_decryption_text)
async def process_decryption_text(message: types.Message, state: FSMContext):
    """Обработка зашифрованного текста"""
    encrypted_text = message.text
    user_id = message.from_user.id

    try:
        # Пробуем распарсить как JSON
        try:
            encrypted_data = json.loads(encrypted_text)
        except:
            # Если не JSON, предполагаем что это base64 для RSA
            encrypted_data = encrypted_text

        # Определяем тип шифрования
        if isinstance(encrypted_data, dict):
            algorithm = encrypted_data.get('algorithm', '')

            if algorithm in ['AES-256-GCM', 'ChaCha20-Poly1305']:
                # Нужен пароль
                await state.update_data(encrypted_data=encrypted_data)
                await message.answer(
                    "🔑 Отправьте пароль для расшифровки:",
                    parse_mode="HTML"
                )
                await state.set_state(EncryptionStates.waiting_for_decryption_password)
                return

            elif 'encrypted_key' in encrypted_data:
                # Гибридное шифрование
                keys = key_manager.get_user_keys(user_id)
                if not keys:
                    await message.answer("❌ У вас нет ключей!", reply_markup=get_back_button())
                    await state.clear()
                    return

                plaintext = crypto.hybrid_decrypt(encrypted_data, keys['private_key'])

                await message.answer(
                    "✅ <b>Текст расшифрован (Гибридное)</b>\n\n"
                    f"{plaintext.decode('utf-8')}",
                    parse_mode="HTML",
                    reply_markup=get_back_button()
                )
                await state.clear()

        else:
            # RSA шифрование
            keys = key_manager.get_user_keys(user_id)
            if not keys:
                await message.answer("❌ У вас нет ключей!", reply_markup=get_back_button())
                await state.clear()
                return

            ciphertext = crypto.decode_from_telegram(encrypted_text)
            plaintext = crypto.decrypt_rsa(ciphertext, keys['private_key'])

            await message.answer(
                "✅ <b>Текст расшифрован (RSA)</b>\n\n"
                f"{plaintext.decode('utf-8')}",
                parse_mode="HTML",
                reply_markup=get_back_button()
            )
            await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Ошибка расшифровки: {str(e)}\n\n"
            "Убедитесь, что:\n"
            "• Формат данных правильный\n"
            "• Вы используете правильный ключ",
            reply_markup=get_back_button()
        )
        await state.clear()


@dp.message(EncryptionStates.waiting_for_decryption_password)
async def process_decryption_password(message: types.Message, state: FSMContext):
    """Обработка пароля для расшифровки"""
    data = await state.get_data()
    encrypted_data = data.get('encrypted_data')
    password = message.text

    # Удаляем сообщение с паролем
    await message.delete()

    try:
        algorithm = encrypted_data['algorithm']
        ciphertext = crypto.decode_from_telegram(encrypted_data['ciphertext'])
        nonce = crypto.decode_from_telegram(encrypted_data['nonce'])
        salt = crypto.decode_from_telegram(encrypted_data['salt'])

        # Деривация ключа из пароля
        key, _ = crypto.derive_key_from_password(password, salt)

        # Расшифровка
        if algorithm == 'AES-256-GCM':
            plaintext = crypto.decrypt_aes_gcm(ciphertext, key, nonce)
        elif algorithm == 'ChaCha20-Poly1305':
            plaintext = crypto.decrypt_chacha20(ciphertext, key, nonce)
        else:
            raise ValueError("Неизвестный алгоритм")

        await message.answer(
            f"✅ <b>Текст расшифрован ({algorithm})</b>\n\n"
            f"{plaintext.decode('utf-8')}",
            parse_mode="HTML",
            reply_markup=get_back_button()
        )

    except Exception as e:
        await message.answer(
            f"❌ Ошибка расшифровки: {str(e)}\n\n"
            "Возможно, неверный пароль.",
            reply_markup=get_back_button()
        )

    await state.clear()


@dp.callback_query(F.data == "my_keys")
async def show_keys(callback: types.CallbackQuery):
    """Показать ключи пользователя"""
    user_id = callback.from_user.id

    if not key_manager.user_exists(user_id):
        await callback.answer("❌ У вас нет ключей! Используйте /start", show_alert=True)
        return

    keys = key_manager.get_user_keys(user_id)
    public_key = keys['public_key'].decode('utf-8')

    # Preview ключа
    key_lines = public_key.split('\n')
    key_preview = '\n'.join(key_lines[:3] + ['...'] + key_lines[-3:])

    await callback.message.edit_text(
        f"🔑 <b>Ваши ключи шифрования</b>\n\n"
        f"<b>Публичный ключ RSA-4096:</b>\n"
        f"<code>{key_preview}</code>\n\n"
        f"⚠️ Приватный ключ хранится в зашифрованном виде",
        parse_mode="HTML",
        reply_markup=get_back_button()
    )
    await callback.answer()


@dp.callback_query(F.data == "statistics")
async def show_statistics(callback: types.CallbackQuery):
    """Показать статистику"""
    user_id = callback.from_user.id

    if not key_manager.user_exists(user_id):
        await callback.answer("❌ У вас нет данных", show_alert=True)
        return

    stats = key_manager.get_statistics(user_id)

    await callback.message.edit_text(
        f"📊 <b>Ваша статистика</b>\n\n"
        f"📅 Регистрация: {stats.get('registered', 'N/A')}\n"
        f"🕐 Последняя активность: {stats.get('last_used', 'N/A')}\n"
        f"🔗 Общих ключей: {stats.get('shared_keys_count', 0)}\n"
        f"🔐 Сохраненных паролей: {stats.get('saved_passwords_count', 0)}",
        parse_mode="HTML",
        reply_markup=get_back_button()
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def show_help(callback: types.CallbackQuery):
    """Показать помощь"""
    help_text = """
ℹ️ <b>Помощь по использованию бота</b>

<b>Режимы шифрования:</b>

🔐 <b>AES-256-GCM</b>
• Симметричное шифрование с паролем
• Очень безопасно и быстро
• Нужен пароль для расшифровки

🚀 <b>ChaCha20-Poly1305</b>
• Альтернатива AES, часто быстрее
• Симметричное шифрование с паролем
• Отличная безопасность

🔑 <b>RSA-4096</b>
• Асимметричное шифрование
• Ограничение: до 470 байт
• Использует ваш приватный ключ

⚡ <b>Гибридное (RSA+AES)</b>
• Комбинация RSA и AES
• Для текстов любого размера
• Максимальная безопасность

<b>Команды:</b>
/start - Начать работу
/menu - Главное меню
/keys - Показать ключи

<b>Безопасность:</b>
• Все приватные ключи шифруются перед сохранением
• Пароли никогда не хранятся
• Используются современные криптографические стандарты
"""

    await callback.message.edit_text(
        help_text,
        parse_mode="HTML",
        reply_markup=get_back_button()
    )
    await callback.answer()


@dp.callback_query(F.data == "e2e_chat")
async def e2e_chat_menu(callback: types.CallbackQuery):
    """End-to-end шифрованный чат"""
    await callback.message.edit_text(
        "💬 <b>E2E переписка</b>\n\n"
        "Функция в разработке.\n"
        "Позволит безопасно общаться с другими пользователями бота.",
        parse_mode="HTML",
        reply_markup=get_back_button()
    )
    await callback.answer()


@dp.callback_query(F.data == "settings")
async def settings_menu(callback: types.CallbackQuery):
    """Настройки"""
    keyboard = [
        [InlineKeyboardButton(text="🔄 Пересоздать ключи", callback_data="regenerate_keys")],
        [InlineKeyboardButton(text="🗑️ Удалить все данные", callback_data="delete_all_data")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")]
    ]

    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@dp.callback_query(F.data == "regenerate_keys")
async def regenerate_keys(callback: types.CallbackQuery):
    """Пересоздание ключей"""
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name

    # Удаляем старые ключи
    key_manager.delete_user_keys(user_id)

    # Создаем новые
    private_key, public_key = crypto.generate_rsa_keypair()
    symmetric_key = crypto.generate_symmetric_key()
    key_manager.create_user_keys(user_id, username, private_key, public_key, symmetric_key)

    await callback.message.edit_text(
        "✅ Ключи успешно пересозданы!\n\n"
        "⚠️ Старые зашифрованные данные больше нельзя расшифровать.",
        reply_markup=get_back_button()
    )
    await callback.answer()


# ============= ОБРАБОТЧИКИ ФАЙЛОВ =============

@dp.callback_query(F.data == "encrypt_file")
async def encrypt_file_menu(callback: types.CallbackQuery, state: FSMContext):
    """Меню шифрования файла"""
    await callback.message.edit_text(
        "📁 <b>Шифрование файла</b>\n\n"
        "Отправьте файл, который нужно зашифровать:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_file_to_encrypt)
    await callback.answer()


@dp.message(EncryptionStates.waiting_for_file_to_encrypt, F.document)
async def process_file_to_encrypt(message: types.Message, state: FSMContext):
    """Обработка файла для шифрования"""
    document = message.document
    file_size = document.file_size

    # Проверка размера файла (макс 20 МБ для Telegram)
    if file_size > 20 * 1024 * 1024:
        await message.answer(
            "❌ Файл слишком большой! Максимальный размер: 20 МБ",
            reply_markup=get_back_button()
        )
        await state.clear()
        return

    await message.answer("⏳ Загружаю файл...")

    # Скачиваем файл
    file = await bot.get_file(document.file_id)
    file_path = file.file_path

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    await bot.download_file(file_path, tmp_path)

    # Сохраняем информацию о файле
    await state.update_data(
        file_path=tmp_path,
        file_name=document.file_name
    )

    await message.answer(
        f"📄 Файл получен: {document.file_name}\n"
        f"📊 Размер: {file_size / 1024:.2f} КБ\n\n"
        "🔑 Отправьте пароль для шифрования:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_file_password)


@dp.message(EncryptionStates.waiting_for_file_password)
async def process_file_password(message: types.Message, state: FSMContext):
    """Обработка пароля для шифрования файла"""
    data = await state.get_data()
    input_path = data.get('file_path')
    original_name = data.get('file_name')
    password = message.text

    # Удаляем сообщение с паролем
    await message.delete()

    await message.answer("🔐 Шифрую файл...")

    try:
        # Создаем временный файл для зашифрованных данных
        with tempfile.NamedTemporaryFile(delete=False, suffix='.encrypted') as tmp_out:
            output_path = tmp_out.name

        # Шифруем файл
        salt, nonce = file_crypto.encrypt_file_with_password(input_path, output_path, password)

        # Получаем информацию о файле
        file_info = file_crypto.get_encrypted_file_info(output_path)

        # Создаем файл с метаданными
        metadata = {
            'original_name': original_name,
            'salt': crypto.encode_for_telegram(salt),
            'algorithm': 'AES-256-GCM',
            'original_size': file_info.get('original_size', 0)
        }

        metadata_json = json.dumps(metadata, indent=2)

        # Отправляем зашифрованный файл
        encrypted_file = FSInputFile(output_path, filename=f"{original_name}.encrypted")
        await message.answer_document(
            encrypted_file,
            caption=(
                f"✅ <b>Файл зашифрован!</b>\n\n"
                f"📄 Оригинальное имя: {original_name}\n"
                f"🔐 Алгоритм: AES-256-GCM\n"
                f"📊 Размер: {file_info.get('encrypted_size', 0) / 1024:.2f} КБ\n\n"
                f"<b>Метаданные (сохраните!):</b>\n"
                f"<code>{metadata_json}</code>"
            ),
            parse_mode="HTML",
            reply_markup=get_back_button()
        )

        # Удаляем временные файлы
        os.unlink(input_path)
        os.unlink(output_path)

    except Exception as e:
        await message.answer(
            f"❌ Ошибка шифрования файла: {str(e)}",
            reply_markup=get_back_button()
        )

    await state.clear()


@dp.callback_query(F.data == "decrypt_file")
async def decrypt_file_menu(callback: types.CallbackQuery, state: FSMContext):
    """Меню расшифровки файла"""
    await callback.message.edit_text(
        "📂 <b>Расшифровка файла</b>\n\n"
        "Отправьте зашифрованный файл:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_file_to_decrypt)
    await callback.answer()


@dp.message(EncryptionStates.waiting_for_file_to_decrypt, F.document)
async def process_file_to_decrypt(message: types.Message, state: FSMContext):
    """Обработка зашифрованного файла"""
    document = message.document

    await message.answer("⏳ Загружаю файл...")

    # Скачиваем файл
    file = await bot.get_file(document.file_id)
    file_path = file.file_path

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    await bot.download_file(file_path, tmp_path)

    # Сохраняем информацию о файле
    await state.update_data(file_path=tmp_path)

    await message.answer(
        "📄 Файл получен!\n\n"
        "🔑 Отправьте пароль для расшифровки:",
        parse_mode="HTML"
    )
    await state.set_state(EncryptionStates.waiting_for_decrypt_file_password)


@dp.message(EncryptionStates.waiting_for_decrypt_file_password)
async def process_decrypt_file_password(message: types.Message, state: FSMContext):
    """Обработка пароля для расшифровки файла"""

    # Проверяем, есть ли метаданные в сообщении
    password = None
    salt = None
    original_name = "decrypted_file"

    # Пытаемся распарсить как JSON (если пользователь отправил метаданные вместе с паролем)
    try:
        data_text = message.text

        # Если это JSON с метаданными
        if '{' in data_text and '}' in data_text:
            # Извлекаем JSON
            json_start = data_text.find('{')
            json_end = data_text.rfind('}') + 1
            metadata = json.loads(data_text[json_start:json_end])

            salt_encoded = metadata.get('salt')
            if salt_encoded:
                salt = crypto.decode_from_telegram(salt_encoded)
            original_name = metadata.get('original_name', 'decrypted_file')

            # Пароль - это текст до или после JSON
            password_part = data_text[:json_start] + data_text[json_end:]
            password = password_part.strip()
        else:
            password = data_text
    except:
        password = message.text

    # Удаляем сообщение с паролем
    await message.delete()

    # Если нет salt, просим предоставить метаданные
    if salt is None:
        await message.answer(
            "⚠️ Не найдены метаданные файла (salt).\n\n"
            "Отправьте сообщение в формате:\n"
            "<code>пароль {\"salt\": \"...\", \"original_name\": \"...\"}</code>\n\n"
            "Или просто JSON с метаданными:",
            parse_mode="HTML",
            reply_markup=get_back_button()
        )
        return

    data = await state.get_data()
    input_path = data.get('file_path')

    await message.answer("🔓 Расшифровываю файл...")

    try:
        # Создаем временный файл для расшифрованных данных
        with tempfile.NamedTemporaryFile(delete=False) as tmp_out:
            output_path = tmp_out.name

        # Расшифровываем файл
        file_crypto.decrypt_file_with_password(input_path, output_path, password, salt)

        # Получаем размер файла
        file_size = os.path.getsize(output_path)

        # Отправляем расшифрованный файл
        decrypted_file = FSInputFile(output_path, filename=original_name)
        await message.answer_document(
            decrypted_file,
            caption=(
                f"✅ <b>Файл расшифрован!</b>\n\n"
                f"📄 Имя: {original_name}\n"
                f"📊 Размер: {file_size / 1024:.2f} КБ"
            ),
            parse_mode="HTML",
            reply_markup=get_back_button()
        )

        # Удаляем временные файлы
        os.unlink(input_path)
        os.unlink(output_path)

    except Exception as e:
        await message.answer(
            f"❌ Ошибка расшифровки файла: {str(e)}\n\n"
            "Возможно:\n"
            "• Неверный пароль\n"
            "• Неверные метаданные\n"
            "• Файл поврежден",
            reply_markup=get_back_button()
        )

    await state.clear()


# ============= ЗАПУСК БОТА =============

async def main():
    """Запуск бота"""
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

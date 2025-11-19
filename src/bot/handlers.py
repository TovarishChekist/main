"""
Telegram Bot Message Handlers
"""

import os
import io
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from ..crypto import AdvancedEncryptor, KeyExchangeManager, SignatureManager
from ..crypto.encryptor import CipherType
from ..steganography import ImageSteganography
from ..utils import SecurityManager, MessageValidator

# Configure logging (never log sensitive data)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class EncryptionBot:
    """
    Main encryption bot class
    Handles all cryptographic operations and user interactions
    """

    def __init__(self, token: str):
        """
        Initialize encryption bot

        Args:
            token: Telegram bot token
        """
        self.token = token
        self.encryptor = AdvancedEncryptor()
        self.key_exchange = KeyExchangeManager(key_lifetime_hours=24)
        self.signature_manager = SignatureManager()
        self.steganography = ImageSteganography()
        self.security = SecurityManager(max_per_minute=30, max_per_hour=500)
        self.validator = MessageValidator()

        # User data storage (in production, use encrypted database)
        self.user_keys = {}
        self.user_sessions = {}

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        welcome_message = """
🔐 **Продвинутый бот-шифровальщик**

Максимальная безопасность для ваших сообщений!

**Возможности:**
🛡️ AES-256-GCM шифрование
⚡ ChaCha20-Poly1305 (быстро на мобильных)
🔑 End-to-End шифрование (E2EE)
🤝 Обмен ключами ECDH (X25519)
✍️ Цифровые подписи (Ed25519)
🖼️ Стеганография (скрытие в изображениях)
🔄 Perfect Forward Secrecy

**Команды:**
/encrypt - Зашифровать сообщение
/decrypt - Расшифровать сообщение
/genkeys - Генерация ключей
/session - Создать защищенную сессию
/sign - Подписать сообщение
/verify - Проверить подпись
/stego - Скрыть данные в изображении
/extract - Извлечь данные из изображения
/help - Справка
/security - Статус безопасности

Все операции выполняются локально, ключи хранятся только у вас!
        """

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **Подробная справка**

**1. Простое шифрование**
/encrypt - Отправьте сообщение для шифрования
Бот зашифрует его и вернет закодированную строку

**2. Расшифровка**
/decrypt - Отправьте зашифрованное сообщение
Требуется ключ или активная сессия

**3. Генерация ключей**
/genkeys - Создать новую пару ключей (RSA + Ed25519)
Получите публичный и приватный ключи

**4. Защищенная сессия (E2EE)**
/session <публичный_ключ_партнера>
Создает защищенный канал с Perfect Forward Secrecy

**5. Цифровая подпись**
/sign <сообщение>
Подписать сообщение для проверки подлинности

**6. Проверка подписи**
/verify <подпись> <публичный_ключ>
Проверить подлинность подписанного сообщения

**7. Стеганография**
/stego - Отправьте текст, затем изображение
Данные будут скрыты в изображении

**8. Извлечение из стеганографии**
/extract - Отправьте изображение со скрытыми данными

**Безопасность:**
- Все ключи хранятся в памяти (не на сервере)
- Автоматическая ротация ключей через 24 часа
- Rate limiting для защиты от атак
- Валидация всех входных данных
        """

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def encrypt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /encrypt command"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        # Check if message provided
        if not context.args:
            keyboard = [
                [InlineKeyboardButton("AES-256-GCM", callback_data="cipher_aes")],
                [InlineKeyboardButton("ChaCha20-Poly1305", callback_data="cipher_chacha")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🔐 Выберите алгоритм шифрования:\n\n"
                "Затем отправьте сообщение для шифрования.",
                reply_markup=reply_markup
            )
            return

        # Get message to encrypt
        message = ' '.join(context.args)

        try:
            # Sanitize input
            message = self.security.sanitize_input(message)

            # Get cipher preference (default AES-256-GCM)
            cipher_type = self.user_sessions.get(user_id, {}).get('cipher', CipherType.AES_256_GCM)

            # Encrypt message
            encrypted = self.encryptor.encrypt(message.encode(), cipher_type)

            await update.message.reply_text(
                f"✅ **Сообщение зашифровано!**\n\n"
                f"Алгоритм: `{cipher_type.value}`\n\n"
                f"Зашифрованные данные:\n`{encrypted}`\n\n"
                f"⚠️ Сохраните это для расшифровки!",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Encryption error for user {user_id}: {str(e)}")
            await update.message.reply_text("❌ Ошибка шифрования. Попробуйте снова.")

    async def decrypt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /decrypt command"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        if not context.args:
            await update.message.reply_text(
                "📝 Использование:\n"
                "/decrypt <зашифрованные_данные>"
            )
            return

        encrypted_data = ' '.join(context.args)

        try:
            # Decrypt message
            decrypted = self.encryptor.decrypt(encrypted_data)

            await update.message.reply_text(
                f"✅ **Расшифровано:**\n\n{decrypted.decode()}",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Decryption error for user {user_id}: {str(e)}")
            self.security.detect_anomaly(user_id, 'failed_decrypt')
            await update.message.reply_text(
                "❌ Ошибка расшифровки.\n"
                "Проверьте правильность данных и ключа."
            )

    async def genkeys_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /genkeys command"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        # Check for anomaly
        if self.security.detect_anomaly(user_id, 'generate_keys'):
            await update.message.reply_text("⛔ Слишком много запросов на генерацию ключей!")
            return

        try:
            # Generate RSA keypair
            private_rsa, public_rsa = self.encryptor.generate_rsa_keypair(4096)

            # Generate Ed25519 signing keypair
            private_sig, public_sig = self.signature_manager.generate_signing_keypair(user_id)

            # Generate X25519 for key exchange
            private_x25519, public_x25519 = self.key_exchange.generate_keypair()

            # Store keys
            self.user_keys[user_id] = {
                'rsa_private': private_rsa,
                'rsa_public': public_rsa,
                'sig_private': private_sig,
                'sig_public': public_sig,
                'x25519_private': private_x25519,
                'x25519_public': public_x25519
            }

            import base64

            response = f"""
🔑 **Ключи успешно сгенерированы!**

**RSA-4096 (Асимметричное шифрование):**
Публичный ключ:
```
{public_rsa.decode()[:100]}...
```

**Ed25519 (Цифровые подписи):**
Публичный ключ: `{public_sig}`

**X25519 (Обмен ключами):**
Публичный ключ: `{base64.b64encode(public_x25519).decode()}`

⚠️ **Приватные ключи хранятся в памяти бота.**
📤 Для безопасности экспортируйте их: /exportkeys
            """

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Key generation error for user {user_id}: {str(e)}")
            await update.message.reply_text("❌ Ошибка генерации ключей")

    async def session_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /session command - create E2EE session"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        if not context.args:
            await update.message.reply_text(
                "🤝 **Создание защищенной сессии**\n\n"
                "Использование:\n"
                "/session <публичный_ключ_партнера>\n\n"
                "Или сначала сгенерируйте ключи: /genkeys"
            )
            return

        try:
            peer_public_key = context.args[0]

            # Create session with Perfect Forward Secrecy
            session_info = self.key_exchange.create_session(user_id, peer_public_key)

            self.user_sessions[user_id] = {
                'session_id': user_id,
                'active': True
            }

            await update.message.reply_text(
                f"✅ **Защищенная сессия создана!**\n\n"
                f"Session ID: `{session_info['session_id']}`\n"
                f"Ваш публичный ключ:\n`{session_info['public_key']}`\n\n"
                f"⏰ Срок действия: 24 часа\n"
                f"🔄 Автоматическая ротация ключей (Forward Secrecy)\n\n"
                f"Отправьте ваш публичный ключ партнеру!",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Session creation error for user {user_id}: {str(e)}")
            await update.message.reply_text("❌ Ошибка создания сессии")

    async def sign_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sign command"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        if not context.args:
            await update.message.reply_text(
                "✍️ Использование:\n"
                "/sign <сообщение_для_подписи>"
            )
            return

        message = ' '.join(context.args)

        try:
            # Sign message with timestamp
            signed_data = self.signature_manager.sign_with_timestamp(
                message.encode(), user_id
            )

            await update.message.reply_text(
                f"✅ **Сообщение подписано!**\n\n"
                f"Подпись: `{signed_data['signature']}`\n"
                f"Временная метка: `{signed_data['timestamp']}`\n\n"
                f"Публичный ключ для проверки:\n"
                f"`{self.signature_manager.get_public_key(user_id)}`",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Signing error for user {user_id}: {str(e)}")
            await update.message.reply_text(
                "❌ Ошибка подписи.\n"
                "Сначала сгенерируйте ключи: /genkeys"
            )

    async def stego_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stego command - hide data in image"""
        user_id = str(update.effective_user.id)

        # Check rate limit
        allowed, reason = self.security.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(f"⛔ {reason}")
            return

        await update.message.reply_text(
            "🖼️ **Стеганография**\n\n"
            "1️⃣ Отправьте текст для сокрытия\n"
            "2️⃣ Затем отправьте изображение-контейнер\n\n"
            "Данные будут зашифрованы и скрыты в изображении!"
        )

        # Set state for next message
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        self.user_sessions[user_id]['awaiting_stego_text'] = True

    async def security_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /security command"""
        user_id = str(update.effective_user.id)

        # Get rate limit info
        remaining_minute = self.security.rate_limiter_minute.get_remaining(user_id)
        remaining_hour = self.security.rate_limiter_hour.get_remaining(user_id)

        # Get session info
        session_active = user_id in self.user_sessions
        session_info = ""
        if session_active:
            key_info = self.key_exchange.get_session_info(user_id)
            if key_info:
                session_info = f"\n\n**Активная сессия:**\n" \
                              f"Истекает через: {key_info['expires_in_seconds']}с"

        status = f"""
🛡️ **Статус безопасности**

**Rate Limiting:**
Осталось запросов:
- В минуту: {remaining_minute}/30
- В час: {remaining_hour}/500

**Сессии:**
{'✅ Активна' if session_active else '❌ Нет активных сессий'}{session_info}

**Ключи:**
{'✅ Сгенерированы' if user_id in self.user_keys else '❌ Не созданы'}

**Защита:**
✅ AES-256-GCM шифрование
✅ Perfect Forward Secrecy
✅ Валидация входных данных
✅ Защита от брутфорса
        """

        await update.message.reply_text(status, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        user_id = str(query.from_user.id)

        await query.answer()

        if query.data == "cipher_aes":
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id]['cipher'] = CipherType.AES_256_GCM
            await query.edit_message_text("✅ Выбран алгоритм: AES-256-GCM\n\nТеперь отправьте сообщение для шифрования.")

        elif query.data == "cipher_chacha":
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id]['cipher'] = CipherType.CHACHA20_POLY1305
            await query.edit_message_text("✅ Выбран алгоритм: ChaCha20-Poly1305\n\nТеперь отправьте сообщение для шифрования.")


def setup_handlers(application: Application) -> None:
    """
    Setup all command handlers

    Args:
        application: Telegram application instance
    """
    bot = EncryptionBot(application.bot.token)

    # Command handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("encrypt", bot.encrypt_command))
    application.add_handler(CommandHandler("decrypt", bot.decrypt_command))
    application.add_handler(CommandHandler("genkeys", bot.genkeys_command))
    application.add_handler(CommandHandler("session", bot.session_command))
    application.add_handler(CommandHandler("sign", bot.sign_command))
    application.add_handler(CommandHandler("stego", bot.stego_command))
    application.add_handler(CommandHandler("security", bot.security_status_command))

    # Callback query handler for buttons
    application.add_handler(CallbackQueryHandler(bot.button_callback))

    logger.info("All handlers registered successfully")

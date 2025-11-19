#!/usr/bin/env python3
"""
Advanced Telegram Encryption Bot
Main entry point

Features:
- Multi-algorithm encryption (AES-256-GCM, ChaCha20-Poly1305)
- End-to-End Encryption (E2EE)
- Perfect Forward Secrecy
- Digital Signatures (Ed25519)
- Steganography
- Rate limiting and security
"""

import os
import sys
import logging
from dotenv import load_dotenv

from telegram.ext import Application

from src.bot import setup_handlers


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def validate_environment() -> bool:
    """
    Validate required environment variables

    Returns:
        True if all required vars are set
    """
    required_vars = ['TELEGRAM_BOT_TOKEN']

    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Missing required environment variable: {var}")
            return False

    return True


def main():
    """Main function to start the bot"""

    # Load environment variables
    load_dotenv()

    logger.info("Starting Advanced Telegram Encryption Bot...")

    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Please check .env file")
        sys.exit(1)

    # Get bot token
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    try:
        # Create application
        application = Application.builder().token(token).build()

        # Setup handlers
        setup_handlers(application)

        logger.info("Bot initialized successfully")
        logger.info("Security features enabled:")
        logger.info("  ✓ AES-256-GCM encryption")
        logger.info("  ✓ ChaCha20-Poly1305 encryption")
        logger.info("  ✓ RSA-4096 asymmetric encryption")
        logger.info("  ✓ X25519 key exchange (ECDH)")
        logger.info("  ✓ Ed25519 digital signatures")
        logger.info("  ✓ Perfect Forward Secrecy")
        logger.info("  ✓ Steganography support")
        logger.info("  ✓ Rate limiting protection")
        logger.info("  ✓ Input validation and sanitization")

        # Start bot
        logger.info("Starting polling...")
        application.run_polling(allowed_updates=True)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

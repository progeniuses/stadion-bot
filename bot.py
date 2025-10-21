import os
import sys
import time
import logging
from telebot import TeleBot
from config import BOT_TOKEN, ADMIN_PASSWORD
from db import init_db, Base  # Yangi import
from handlers.registration import register_handlers
from handlers.booking import booking_handlers
from handlers.admin import admin_handlers
from scheduler import start_reminder_scheduler

# Add handlers directory to path
sys.path.append(os.path.dirname(__file__))

# Logging sozlash
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot
logger.info("🤖 Bot ishga tushmoqda....")

if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    logger.error("❌ BOT_TOKEN o'rnatilmagan!")
    logger.error("Environment variable o'rnating: Render dashboard'da qo‘shing")
    sys.exit(1)

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')

# User states
states = {}

# PostgreSQL ulanishini sozlash
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine, SessionLocal = init_db()  # init_db dan engine va session olish
    Base.metadata.create_all(engine)  # Jadvallarni yaratish
else:
    logger.warning("⚠ DATABASE_URL aniqlanmadi, baza ulanmagan!")

# Register all handlers
register_handlers(bot, states)
booking_handlers(bot, states)
admin_handlers(bot, states)

# Start reminder scheduler
start_reminder_scheduler(bot)

logger.info("✅ Bot tayyor!")
logger.info("📡 Polling boshlandi...")
logger.info("⏰ Eslatma tizimi faol!")

# Start polling with retry
if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            logger.info("\n🔄 Bot qayta ishga tushmoqda...")
            time.sleep(10)  # 10 soniya kutib, qayta urinish
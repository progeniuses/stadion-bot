import telebot
from config import BOT_TOKEN
import sys
import os
import logging
import time


# Add handlers directory to path
sys.path.append(os.path.dirname(__file__))

# Import handlers
from handlers.registration import register_handlers
from handlers.booking import booking_handlers
from handlers.admin import admin_handlers
from scheduler import start_reminder_scheduler

# Initialize bot
logging.info("🤖 Bot ishga tushmoqda...")

if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    logging.error("❌ BOT_TOKEN o'rnatilmagan!")
    logging.error("Environment variable o'rnating:")
    logging.error("Windows: $env:BOT_TOKEN = 'your_token'")
    logging.error("Linux/Mac: export BOT_TOKEN='your_token'")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# User states
states = {}

# Register all handlers
register_handlers(bot, states)
booking_handlers(bot, states)
admin_handlers(bot, states)

# Start reminder scheduler
start_reminder_scheduler(bot)

logging.info("✅ Bot tayyor!")
logging.info("📡 Polling boshlandi...")
logging.info("⏰ Eslatma tizimi faol!")

# Start polling with retry
if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(f"❌ Xatolik: {e}")
            logging.info("\n🔄 Bot qayta ishga tushmoqda...")
            time.sleep(10)  # 10 soniya kutib, qayta urinish
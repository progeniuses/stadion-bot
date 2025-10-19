import os
from dotenv import load_dotenv  # Qo'shildi

load_dotenv()  # .env fayldan o'qish

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///postgres.db')

# ========== STADIUM SETTINGS ==========
FIELDS = ['1-stadion', '2-stadion', '3-stadion']

PRICES = {
    '1-stadion': 270000,
    '2-stadion': 210000,
    '3-stadion': 170000
}

# ========== TIME SLOTS ==========
def generate_slots(start_hour=7, end_hour=24):
    """
    Vaqt slotlarini generatsiya qilish
    07:00 dan 00:00 gacha
    """
    slots = []
    for hour in range(start_hour, end_hour):
        start = f"{hour:02d}:00"
        end = f"{(hour+1):02d}:00" if hour < 23 else "00:00"
        slots.append(f"{start}-{end}")
    return slots

SLOTS = generate_slots()  # 07:00-08:00, 08:00-09:00, ..., 23:00-00:00

# ========== BOOKING RULES ==========
CANCEL_DEADLINE_HOUR = 12  # 12:00 gacha bekor qilish mumkin
REMINDER_HOURS_BEFORE = 12  # 12 soat oldin eslatma (ertaga ertalab)

# ========== CALENDAR SETTINGS ==========
DAYS_OF_WEEK = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan', 'Yak']
MONTHS = [
    'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
    'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
]
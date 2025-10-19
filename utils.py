from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import datetime
from config import CANCEL_DEADLINE_HOUR


def main_menu():
    """Asosiy menyu"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚽ Band qilish", "📋 Mening o'yinlarim")
    markup.add("🔐 Admin panel")
    return markup


def admin_menu():
    """Admin menyu"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Barcha o'yinlar", "📊 Statistika")
    markup.add("📈 Grafik statistika", "📥 Excel yuklash")
    markup.add("🗑 O'yinni o'chirish")
    markup.add("🏠 Asosiy menyu")
    return markup


def request_contact():
    """Telefon raqam so'rash"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📱 Raqamni ulashish", request_contact=True)
    markup.add(button)
    return markup


def field_menu():
    """Maydonlar menyusi"""
    from config import FIELDS
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for field in FIELDS:
        markup.add(field.capitalize())
    markup.add("🔙 Orqaga")
    return markup


def slot_menu(slots):
    """Vaqt slotlari menyusi"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for slot in slots:
        markup.add(slot)
    markup.add("🔙 Orqaga")
    return markup


def format_booking_info(booking, user):
    """Booking ma'lumotlarini formatlash"""
    from config import PRICES
    text = (
        f"📅 Sana: {booking.date.strftime('%Y-%m-%d')}\n"
        f"🕐 Vaqt: {booking.slot}\n"
        f"⚽ Maydon: {booking.field.capitalize()}\n"
        f"👤 Mijoz: {user.name} {user.surname}\n"
        f"📞 Telefon: {user.phone}\n"
        f"💰 Narx: {PRICES.get(booking.field, 0):,} so'm"
    )
    return text


def check_cancel_time(booking):
    """
    Bekor qilish mumkinligini tekshirish
    YANGI QOIDA: Faqat soat 12:00 gacha bekor qilish mumkin
    """
    now = datetime.datetime.now()

    # Bugungi slot uchun
    if booking.date == now.date():
        # Bugun soat 12:00 o'tgan bo'lsa, bekor qilib bo'lmaydi
        deadline = datetime.datetime.combine(now.date(), datetime.time(CANCEL_DEADLINE_HOUR, 0))
        if now >= deadline:
            return False, f"⚠️ Bugungi o'yinlar soat {CANCEL_DEADLINE_HOUR}:00 dan keyin bekor qilolmaysiz!"

    # Ertaga yoki undan keyin bo'lsa
    elif booking.date > now.date():
        # Booking kunidan oldingi kun soat 12:00 gacha bekor qilish mumkin
        booking_day_before = booking.date - datetime.timedelta(days=1)
        deadline = datetime.datetime.combine(booking_day_before, datetime.time(CANCEL_DEADLINE_HOUR, 0))

        if now >= deadline:
            return False, f"⚠️ Rejalashtirilgan o'yin kunidan oldingi kun soat {CANCEL_DEADLINE_HOUR}:00 gacha bekor qilish mumkin edi!"

    # O'tgan kunlar uchun
    else:
        return False, "⚠️ O'tgan o'yinni bekor qilolmaysiz!"

    return True, None
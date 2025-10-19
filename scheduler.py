import datetime
import time
import threading
from db import get_session, Booking, get_user_by_id  # Import optim

def check_and_send_reminders(bot):
    while True:
        try:
            now = datetime.datetime.now()
            tomorrow = (now + datetime.timedelta(days=1)).date()

            session = get_session()
            try:
                # Optim: Faqat ertangi bookinglarni olish (get_all_bookings o'rniga)
                bookings = session.query(Booking).filter(Booking.date == tomorrow).all()

                for booking in bookings:
                    slot_time_str = booking.slot.split('-')[0]
                    slot_time = datetime.datetime.strptime(slot_time_str, "%H:%M").time()
                    slot_datetime = datetime.datetime.combine(booking.date, slot_time)
                    reminder_time = slot_datetime - datetime.timedelta(hours=12)
                    time_diff = abs((reminder_time - now).total_seconds())

                    if time_diff < 300:
                        user = get_user_by_id(booking.user_id)
                        if user:
                            message = (
                                f"⏰ Eslatma!\n\n"
                                f"Ertaga sizning o'yingiz  bor:\n\n"
                                f"📅 Sana: {booking.date}\n"
                                f"🕐 Vaqt: {booking.slot}\n"
                                f"⚽ Maydon: {booking.field.capitalize()}\n\n"
                                f"Vaqtida keling! 👍"
                            )
                            bot.send_message(user.telegram_id, message)
                            print(f"✅ Eslatma yuborildi: User {user.telegram_id}, Booking {booking.id}")
            finally:
                session.close()

            time.sleep(300)
        except Exception as e:
            print(f"❌ Scheduler xatosi: {e}")
            time.sleep(300)

# Qolgan kod o'zgarmas


def start_reminder_scheduler(bot):
    """
    Eslatma schedulerni alohida thread da ishga tushirish
    """
    reminder_thread = threading.Thread(target=check_and_send_reminders, args=(bot,), daemon=True)
    reminder_thread.start()
    print("✅ Eslatma scheduler ishga tushdi!")
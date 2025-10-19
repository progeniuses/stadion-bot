import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import (get_user, add_booking, get_user_bookings,
                get_booking_by_id, delete_booking, get_booked_slots)
from config import FIELDS, PRICES, SLOTS
from utils import field_menu, slot_menu, check_cancel_time, format_booking_info, main_menu
from calendar_keyboard import create_calendar, separate_callback_data


def is_slot_available(date, slot):
    """
    Slotni band qilish mumkinligini tekshirish
    Agar bugun bo'lsa, faqat hozirgi vaqtdan keyingilarini ko'rsatish
    """
    now = datetime.datetime.now()

    # Agar bugun bo'lsa
    if date == now.date():
        # Slot boshlanish vaqtini olish: "21:00-22:00" -> 21:00
        slot_start_time = slot.split('-')[0]
        slot_hour = int(slot_start_time.split(':')[0])
        slot_minute = int(slot_start_time.split(':')[1])

        slot_datetime = datetime.datetime.combine(
            date,
            datetime.time(slot_hour, slot_minute)
        )

        # Agar slot vaqti o'tib ketgan bo'lsa yoki hozir bo'lsa
        if slot_datetime <= now:
            return False

    return True


def is_booking_active(booking):
    """
    Bookingning faol yoki o'tgan ekanligini tekshirish
    """
    now = datetime.datetime.now()

    # Booking tugash vaqtini hisoblash
    slot_end_time = booking.slot.split('-')[1]  # "21:00-22:00" -> "22:00"
    end_hour = int(slot_end_time.split(':')[0])
    end_minute = int(slot_end_time.split(':')[1])

    booking_end = datetime.datetime.combine(
        booking.date,
        datetime.time(end_hour, end_minute)
    )

    # Agar booking tugagan bo'lsa
    return booking_end > now


def booking_handlers(bot, states):
    @bot.message_handler(func=lambda m: m.text == "⚽ Band qilish")
    def start_booking(message):
        user_id = message.from_user.id
        user = get_user(user_id)

        if not user:
            bot.send_message(user_id, "❌ Avval ro'yxatdan o'ting: /register")
            return

        # Show calendar
        bot.send_message(
            user_id,
            "📅 Kunni tanlang:",
            reply_markup=create_calendar()
        )
        states[user_id] = {'step': 'select_date'}

    # Calendar navigation
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_nav_'))
    def calendar_navigation(call):
        parts = call.data.split('_')
        year, month = int(parts[2]), int(parts[3])

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_calendar(year, month)
        )
        bot.answer_callback_query(call.id)

    # Calendar day selection
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_day_'))
    def calendar_day_select(call):
        user_id = call.from_user.id
        year, month, day = separate_callback_data(call.data)

        if not year:
            bot.answer_callback_query(call.id, "❌ Xatolik!")
            return

        selected_date = datetime.date(year, month, day)

        # Delete calendar message
        bot.delete_message(call.message.chat.id, call.message.message_id)

        # Save date and ask for field
        states[user_id] = {
            'step': 'select_field',
            'date': selected_date
        }

        bot.send_message(
            user_id,
            f"✅ Tanlangan kun: {selected_date.strftime('%Y-%m-%d')}\n\n"
            "⚽ Maydonni tanlang:",
            reply_markup=field_menu()
        )
        bot.answer_callback_query(call.id)

    # Calendar cancel
    @bot.callback_query_handler(func=lambda call: call.data == 'calendar_cancel')
    def calendar_cancel(call):
        user_id = call.from_user.id
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, "❌ Bekor qilindi.", reply_markup=main_menu())
        if user_id in states:
            del states[user_id]
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'ignore')
    def ignore_callback(call):
        bot.answer_callback_query(call.id)

    # Field selection - FIX: Orqaga tugmasi kalendarga olib boradi
    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'select_field')
    def select_field(message):
        user_id = message.from_user.id
        field_text = message.text.strip().lower()  # Case-insensitive

        # FIX: Orqaga tugmasi - kalendarga qaytarish
        if field_text in ["🔙 orqaga", "orqaga", "back"]:
            bot.send_message(
                user_id,
                "📅 Kunni tanlang:",
                reply_markup=create_calendar()
            )
            states[user_id]['step'] = 'select_date'
            return

        # Field ni lowercase ga o'tkazish
        field = field_text

        if field not in FIELDS:
            bot.send_message(
                user_id,
                "❌ Noto'g'ri maydon! Qaytadan tanlang:",
                reply_markup=field_menu()
            )
            return

        date = states[user_id]['date']

        # Get booked slots
        booked = get_booked_slots(date, field)

        # FIX: O'tgan vaqtlarni filter qilish
        available_slots = []
        for s in SLOTS:
            if s not in booked and is_slot_available(date, s):
                available_slots.append(s)

        if not available_slots:
            now = datetime.datetime.now()
            if date == now.date():
                bot.send_message(
                    user_id,
                    "😞 Bugun uchun bo'sh vaqt qolmadi.\n"
                    "Boshqa kun yoki maydon tanlang:",
                    reply_markup=field_menu()
                )
            else:
                bot.send_message(
                    user_id,
                    "😞 Bu maydon uchun bo'sh vaqt yo'q.\n"
                    "Boshqa maydon tanlang:",
                    reply_markup=field_menu()
                )
            return

        states[user_id]['field'] = field
        states[user_id]['step'] = 'select_slot'

        bot.send_message(
            user_id,
            f"⚽ Maydon: {field.capitalize()}\n"
            f"💰 Narx: {PRICES[field]:,} so'm\n\n"
            f"🕐 Bo'sh vaqtlardan birini tanlang:",
            reply_markup=slot_menu(available_slots)
        )

    # Slot selection - FIX: Orqaga tugmasi to'liq ishlaydi
    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'select_slot')
    def select_slot(message):
        user_id = message.from_user.id
        slot = message.text.strip()

        # FIX: Orqaga tugmasi (case-insensitive)
        if slot.lower() in ["🔙 orqaga", "orqaga", "back"]:
            date = states[user_id]['date']
            bot.send_message(
                user_id,
                f"✅ Kun: {date.strftime('%Y-%m-%d')}\n\n"
                "⚽ Maydonni tanlang:",
                reply_markup=field_menu()
            )
            states[user_id]['step'] = 'select_field'
            return

        date = states[user_id]['date']
        field = states[user_id]['field']
        user = get_user(user_id)

        # FIX: Yana bir bor vaqtni tekshirish
        if not is_slot_available(date, slot):
            bot.send_message(
                user_id,
                "❌ Bu vaqt allaqachon o'tib ketgan!\n"
                "Boshqa vaqt tanlang:"
            )
            return

        # Book
        booking_id = add_booking(user.id, date, field, slot)
        if booking_id:
            # Excel ga qo'shish
            from excel_manager import append_booking_to_excel
            append_booking_to_excel(booking_id)

            bot.send_message(
                user_id,
                f"✅ Muvaffaqiyatli band qilindi!\n\n"
                f"📅 Sana: {date}\n"
                f"🕐 Vaqt: {slot}\n"
                f"⚽ Maydon: {field.capitalize()}\n"
                f"💰 Narx: {PRICES[field]:,} so'm\n\n"
                f"💵 To'lovni stadiondan naqd amalga oshiring.",
                reply_markup=main_menu()
            )
            del states[user_id]
        else:
            bot.send_message(
                user_id,
                "❌ Bu vaqt hozirgina band qilindi!\n"
                "Boshqa vaqt tanlang:"
            )

    # My bookings - FIX: Faqat faol bookinglar ko'rsatiladi
    @bot.message_handler(func=lambda m: m.text == "📋 Mening o\'yinlarim")
    def my_bookings(message):
        user_id = message.from_user.id
        user = get_user(user_id)

        if not user:
            bot.send_message(user_id, "❌ Avval ro'yxatdan o'ting: /register")
            return

        all_bookings = get_user_bookings(user.id)

        # FIX: Faqat faol bookinglarni filter qilish
        active_bookings = [b for b in all_bookings if is_booking_active(b)]

        if not active_bookings:
            bot.send_message(user_id, "📋 Sizda faol rejalashtirilgan o\'yin yo'q.")
            return

        markup = InlineKeyboardMarkup()
        for b in active_bookings:
            text = f"📅 {b.date} | 🕐 {b.slot} | ⚽ {b.field.capitalize()}"
            markup.add(InlineKeyboardButton(
                text,
                callback_data=f"view_booking_{b.id}"
            ))

        bot.send_message(
            user_id,
            "📋 Sizning faol o'yinlarim:\n\n"
            "Ko'rish uchun o'yinlarim ustiga bosing:",
            reply_markup=markup
        )

    # View booking details
    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_booking_'))
    def view_booking(call):
        booking_id = int(call.data.split('_')[2])
        booking = get_booking_by_id(booking_id)

        if not booking:
            bot.answer_callback_query(call.id, "❌ Rejalashtirilgan o\'yin topilmadi!")
            return

        # FIX: Agar booking allaqachon o'tgan bo'lsa
        if not is_booking_active(booking):
            bot.edit_message_text(
                "⚠️ Bu o\'yin allaqachon tugagan.",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id, "O\'yin tugagan")
            return

        user = get_user(call.from_user.id)
        text = format_booking_info(booking, user)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            "🗑 Bekor qilish",
            callback_data=f"cancel_booking_{booking_id}"
        ))
        markup.add(InlineKeyboardButton(
            "🔙 Orqaga",
            callback_data="back_to_bookings"
        ))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    # Cancel booking
    @bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_booking_'))
    def cancel_booking(call):
        user_id = call.from_user.id
        booking_id = int(call.data.split('_')[2])
        booking = get_booking_by_id(booking_id)

        if not booking:
            bot.answer_callback_query(call.id, "❌ O\'yin topilmadi!")
            return

        # FIX: Booking tugaganligini tekshirish
        if not is_booking_active(booking):
            bot.answer_callback_query(call.id, "❌ O\'yin allaqachon tugagan!", show_alert=True)
            return

        user = get_user(user_id)
        if booking.user_id != user.id:
            bot.answer_callback_query(call.id, "❌ Bu sizning o\'yiningiz emas!")
            return

        # Check time (12:00 gacha)
        can_cancel, error_msg = check_cancel_time(booking)
        if not can_cancel:
            bot.answer_callback_query(call.id, error_msg, show_alert=True)
            return

        # Delete
        if delete_booking(booking_id):
            bot.edit_message_text(
                "✅ O\'yin bekor qilindi!",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id, "✅ Bekor qilindi!")
        else:
            bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi!")

    # Back to bookings list
    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_bookings')
    def back_to_bookings(call):
        user_id = call.from_user.id
        user = get_user(user_id)

        if not user:
            bot.answer_callback_query(call.id, "❌ Xatolik!")
            return

        all_bookings = get_user_bookings(user.id)

        # FIX: Faqat faol bookinglar
        active_bookings = [b for b in all_bookings if is_booking_active(b)]

        if not active_bookings:
            bot.edit_message_text(
                "📋 Sizda faol o\'yinlar yo'q.",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id)
            return

        markup = InlineKeyboardMarkup()
        for b in active_bookings:
            text = f"📅 {b.date} | 🕐 {b.slot} | ⚽ {b.field.capitalize()}"
            markup.add(InlineKeyboardButton(
                text,
                callback_data=f"view_booking_{b.id}"
            ))

        bot.edit_message_text(
            "📋 Sizning faol o'yinlaringiz:\n\n"
            "Ko'rish uchun o\'yinlar ustiga bosing:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
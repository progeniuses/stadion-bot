import datetime
import io
from config import ADMIN_PASSWORD, FIELDS, SLOTS, PRICES
from db import get_all_bookings, get_today_stats, get_month_stats, get_user_by_id, get_today_revenue, get_month_revenue
from utils import admin_menu, main_menu
import matplotlib
matplotlib.use('Agg')  # Qo'shildi: Server backend
import logging
# generate_graphic_stats ichida plt.savefig oldin close qilish
# Qolgan truncated kod o'zgarmas, lekin error handling qo'sh
import matplotlib.pyplot as plt


def admin_handlers(bot, states):
    @bot.message_handler(func=lambda m: m.text == "🔐 Admin panel")
    def admin_login(message):
        user_id = message.from_user.id
        bot.send_message(user_id, "🔐 Admin parolini kiriting:")
        states[user_id] = {'step': 'admin_password'}

    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'admin_password')
    def check_password(message):
        user_id = message.from_user.id

        if message.text == ADMIN_PASSWORD:
            states[user_id] = {'step': None, 'is_admin': True}
            bot.send_message(
                user_id,
                "✅ Admin sifatida kirdingiz!",
                reply_markup=admin_menu()
            )
        else:
            bot.send_message(user_id, "❌ Noto'g'ri parol!")
            if user_id in states:
                del states[user_id]

    @bot.message_handler(func=lambda m: m.text == "🏠 Asosiy menyu")
    def back_to_main(message):
        user_id = message.from_user.id
        if user_id in states:
            states[user_id].pop('is_admin', None)
        bot.send_message(
            user_id,
            "🏠 Asosiy menyu:",
            reply_markup=main_menu()
        )

    @bot.message_handler(
        func=lambda m: m.text == "📋 Barcha o\'yinlar" and states.get(m.from_user.id, {}).get('is_admin'))
    def view_all_bookings(message):
        user_id = message.from_user.id
        bookings = get_all_bookings()

        if not bookings:
            bot.send_message(user_id, "📋 Hozircha o'yinlar yo'q.")
            return

        text = "📋 Barcha o\'yinlar:\n\n"

        for b in bookings:
            # FIX: get_user_by_id ishlatildi (user.id orqali, telegram_id emas)
            user = get_user_by_id(b.user_id)

            if user:
                text += f"🆔 ID: {b.id}\n"
                text += f"📅 {b.date} | 🕐 {b.slot}\n"
                text += f"⚽ {b.field.capitalize()}\n"
                text += f"👤 {user.name} {user.surname}\n"
                text += f"📞 {user.phone}\n"
                text += f"💰 {PRICES.get(b.field, 0):,} so'm\n"
                text += "─" * 35 + "\n"
            else:
                text += f"🆔 ID: {b.id}\n"
                text += f"📅 {b.date} | 🕐 {b.slot}\n"
                text += f"⚽ {b.field.capitalize()}\n"
                text += f"👤 (Foydalanuvchi topilmadi)\n"
                text += "─" * 35 + "\n"

        # Send in chunks if too long
        if len(text) > 4000:
            chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                bot.send_message(user_id, chunk)
        else:
            bot.send_message(user_id, text)

    @bot.message_handler(func=lambda m: m.text == "📊 Statistika" and states.get(m.from_user.id, {}).get('is_admin'))
    def show_stats(message):
        user_id = message.from_user.id

        today = datetime.date.today()
        today_stats = get_today_stats()
        month_stats = get_month_stats()

        # Bugungi slotlar
        total_slots = len(SLOTS) * len(FIELDS)
        booked_today = sum(count for _, count in today_stats)

        text = f"📊 Statistika\n{'=' * 35}\n\n"
        text += f"📅 Bugun ({today.strftime('%Y-%m-%d')}):\n"
        text += f"Band: {booked_today}/{total_slots} slot"

        if total_slots > 0:
            percent = (booked_today / total_slots * 100)
            text += f" ({percent:.1f}%)\n"
        else:
            text += "\n"

        # Maydonlar bo'yicha
        if today_stats:
            text += "\n📋 Maydonlar bo'yicha:\n"
            for field, count in today_stats:
                field_slots = len(SLOTS)
                field_percent = (count / field_slots * 100)
                text += f"⚽ {field.capitalize()}: {count}/{field_slots} ({field_percent:.0f}%)\n"
        else:
            text += "\n⚠️ Bugun hali o'yinlar yo'q\n"

        # Oylik stats
        text += f"\n📆 Oylik ({today.strftime('%B %Y')}):\n"
        text += f"Jami o'yinlar: {month_stats} ta\n"

        # Haqiqiy daromad (taxminiy emas)
        month_revenue = get_month_revenue()
        text += f"💰 Oylik daromad: {month_revenue:,} so'm\n"

        today_revenue = get_today_revenue()
        text += f"💵 Bugungi daromad: {today_revenue:,} so'm"

        bot.send_message(user_id, text)

    @bot.message_handler(
        func=lambda m: m.text == "📈 Grafik statistika" and states.get(m.from_user.id, {}).get('is_admin'))
    def show_advanced_stats(message):
        from statistics import get_weekly_stats, get_hourly_stats, get_field_popularity, get_weekly_revenue, get_monthly_trend
        user_id = message.from_user.id

        try:
            # Ma'lumotlarni olish
            weekly = get_weekly_stats()
            hourly = get_hourly_stats()
            fields = get_field_popularity()
            weekly_revenue = get_weekly_revenue()
            monthly = get_monthly_trend()

            # Ma'lumotlarni tayyorlash
            days = [d[0][:2] for d in weekly]  # Qisqa nomlar: "Du", "Se", etc.
            weekly_values = [d[1] for d in weekly]

            times = [h[0] for h in hourly]
            time_values = [h[1] for h in hourly]

            field_names = [f[0].capitalize() for f in fields]
            field_values = [f[1] for f in fields]

            revenue_labels = [w[0] for w in weekly_revenue]
            revenue_values = [w[1] for w in weekly_revenue]

            months = [m[0][:3] for m in monthly]  # Qisqa nomlar: "Apr", "May", etc.
            month_values = [m[1] for m in monthly]

            # Grafiklar chizish
            fig, axes = plt.subplots(5, 1, figsize=(6, 15))
            fig.suptitle("📊 GRAFIK STATISTIKA", fontsize=16, fontweight='bold')

            # 1️⃣ Hafta kunlari
            axes[0].bar(days, weekly_values)
            axes[0].set_title("Hafta Kunlari")
            axes[0].set_ylabel("Soni")

            # 2️⃣ TOP vaqtlar
            axes[1].barh(times, time_values, color="orange")
            axes[1].set_title("TOP Vaqtlar")

            # 3️⃣ Maydon populyarligi
            axes[2].barh(field_names, field_values, color="blue")
            axes[2].set_title("Maydonlar")

            # 4️⃣ Haftalik daromad
            axes[3].bar(revenue_labels, revenue_values, color="purple")
            axes[3].set_title("Haftalik Daromad (ming)")
            axes[3].set_ylabel("Qiymat")

            # 5️⃣ Oylik trend
            axes[4].plot(months, month_values, marker='o', color="green")
            axes[4].set_title("6 Oylik Trend")
            axes[4].set_ylabel("Qiymat")

            plt.tight_layout()
            plt.subplots_adjust(top=0.95)

            # Grafikni saqlash
            file_path = "grafik_stat.png"
            plt.savefig(file_path)
            plt.close()

            # Telegramga yuborish
            with open(file_path, "rb") as photo:
                bot.send_photo(user_id, photo, caption="📈 Grafik statistika yangilandi")

        except Exception as e:
            bot.send_message(user_id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda m: m.text == "📥 Excel yuklash" and states.get(m.from_user.id, {}).get('is_admin'))
    def download_excel(message):
        user_id = message.from_user.id
        try:
            from excel_manager import EXCEL_FILE
            with open(EXCEL_FILE, 'rb') as f:
                bot.send_document(user_id, f, visible_file_name="bookings.xlsx", caption="📊 Barcha bookinglar")
        except Exception as e:
            bot.send_message(user_id, f"❌ Xatolik: {e}")

    # ... fayl boshidagi importlar va oldingi funksiyalar o'zgarmas ...

    @bot.message_handler(
        func=lambda m: m.text == "🗑 O'yinni o'chirish" and states.get(m.from_user.id, {}).get(
            'is_admin'))  # <<<< TO'G'RILASH: "O'yinlarni" -> "O'yinni"
    def delete_booking_start(message):
        user_id = message.from_user.id
        bot.send_message(
            user_id,
            "📝 O'yin ID sini kiriting:\n\n"
            "ID ni olish uchun '📋 Barcha o'yinlar' bo'limiga kiring."
        )
        states[user_id]['step'] = 'admin_delete'

    # ... qolgan kod o'zgarmas ...

    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'admin_delete')
    def delete_booking_confirm(message):
        user_id = message.from_user.id

        try:
            booking_id = int(message.text)
            from db import get_booking_by_id, delete_booking

            booking = get_booking_by_id(booking_id)
            if not booking:
                bot.send_message(user_id, "❌ O'yin topilmadi!")
                return

            # FIX: get_user_by_id ishlatildi
            user = get_user_by_id(booking.user_id)
            text = f"⚠️ Haqiqatan ham o'chirmoqchimisiz?\n\n"
            text += f"🆔 ID: {booking.id}\n"
            text += f"📅 {booking.date}\n"
            text += f"🕐 {booking.slot}\n"
            text += f"⚽ {booking.field.capitalize()}\n"

            if user:
                text += f"👤 {user.name} {user.surname}\n"
                text += f"📞 {user.phone}\n"

            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Ha", callback_data=f"admin_delete_{booking_id}"),
                InlineKeyboardButton("❌ Yo'q", callback_data="admin_cancel_delete")
            )

            bot.send_message(user_id, text, reply_markup=markup)

        except ValueError:
            bot.send_message(user_id, "❌ Faqat raqam kiriting!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_delete_'))
    def admin_delete_confirm(call):
        user_id = call.from_user.id
        booking_id = int(call.data.split('_')[2])

        from db import delete_booking  # <<<< TO'G'RILASH: Import qo'shildi!

        if delete_booking(booking_id):
            bot.edit_message_text(
                "✅ O'yin o'chirildi!",
                call.message.chat.id,
                call.message.message_id
            )
            states[user_id]['step'] = None
        else:
            bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi!")

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_cancel_delete')
    def admin_cancel_delete(call):
        user_id = call.from_user.id
        bot.edit_message_text(
            "❌ Bekor qilindi.",
            call.message.chat.id,
            call.message.message_id
        )
        states[user_id]['step'] = None
        bot.answer_callback_query(call.id)
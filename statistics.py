import datetime
from collections import defaultdict
from db import get_session, Booking, get_user_by_id
from dateutil.relativedelta import relativedelta  # Qo'shildi

def get_weekly_stats():
    """Haftalik statistika - qaysi kunlar ko'proq band qilinadi"""
    session = get_session()
    try:
        # So'nggi 30 kun
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        bookings = session.query(Booking).filter(Booking.date >= start_date).all()

        # Hafta kunlari bo'yicha
        days_count = defaultdict(int)
        days_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']

        for booking in bookings:
            day_of_week = booking.date.weekday()  # 0=Monday
            days_count[day_of_week] += 1

        # Formatlash
        result = []
        for i in range(7):
            result.append((days_names[i], days_count[i]))

        return result
    finally:
        session.close()


def get_hourly_stats():
    """Soatlik statistika - qaysi soatlar ko'proq band qilinadi"""
    session = get_session()
    try:
        # So'nggi 30 kun
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        bookings = session.query(Booking).filter(Booking.date >= start_date).all()

        hours_count = defaultdict(int)

        for booking in bookings:
            # Butun slotni saqlash: "18:00-19:00"
            hours_count[booking.slot] += 1

        # Sort by count descending, keyin top 10
        sorted_slots = sorted(hours_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_slots[:10]  # Faqat top 10
    finally:
        session.close()


def get_field_popularity():
    """Maydon populyarligi"""
    session = get_session()
    try:
        # So'nggi 30 kun
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        bookings = session.query(Booking).filter(Booking.date >= start_date).all()

        field_count = defaultdict(int)

        for booking in bookings:
            field_count[booking.field] += 1

        # Sort by count descending
        result = sorted(field_count.items(), key=lambda x: x[1], reverse=True)
        return result
    finally:
        session.close()




# get_monthly_trend:
def get_monthly_trend():
    session = get_session()
    try:
        result = []
        today = datetime.date.today()

        for i in range(6, -1, -1):
            month_start = (today - relativedelta(months=i)).replace(day=1)  # Tuzatish: Aniqlik
            month_end = month_start + relativedelta(months=1)

            count = session.query(Booking).filter(
                Booking.date >= month_start,
                Booking.date < month_end
            ).count()

            month_name = month_start.strftime('%B')
            result.append((month_name, count))

        return result
    finally:
        session.close()

# Qolgan kod o'zgarmas


def get_weekly_revenue():
    """Haftalik daromad statistikasi"""
    from config import PRICES
    session = get_session()
    try:
        # So'nggi 4 hafta
        result = []

        for week in range(3, -1, -1):
            start_date = datetime.date.today() - datetime.timedelta(days=week * 7 + 6)
            end_date = datetime.date.today() - datetime.timedelta(days=week * 7)

            bookings = session.query(Booking).filter(
                Booking.date >= start_date,
                Booking.date <= end_date
            ).all()

            # Daromadni hisoblash
            revenue = 0
            for b in bookings:
                revenue += PRICES.get(b.field, 0)

            # Hafta nomi
            week_label = f"W{4 - week}"  # W1, W2, W3, W4
            result.append((week_label, revenue // 1000))  # Minglar ichida

        return result
    finally:
        session.close()


def create_text_chart(data, title, max_width=15):
    """
    Gorizontal bar chart - to'g'ri chiziqli versiya
    Barcha label bir xil uzunlikda (16 belgi)
    Barcha grafik bir chiziqdan boshlanadi
    """
    if not data:
        return "Ma'lumot yo'q"

    # Max value topish
    max_val = max(val for _, val in data)
    if max_val == 0:
        max_val = 1

    chart = f"\n📊 {title}\n{'=' * 40}\n\n"

    for label, value in data:
        # Bar uzunligini hisoblash
        bar_length = int((value / max_val) * max_width)
        bar = "█" * bar_length if bar_length > 0 else ""

        # Label ni to'liq 16 belgiga to'ldirish (eng uzun: "18:00-19:00" = 11)
        label_formatted = label[:16].ljust(16)

        # Qiymatni 4 belgiga to'ldirish
        value_str = str(value).rjust(4)

        chart += f"{label_formatted} {bar} {value_str}\n"

    return chart


def generate_statistics_report():
    """
    To'liq statistika hisobotini generatsiya qilish
    Grafiklar orasida bo'shliq bor, hamma narsa bir chiziqda
    """
    report = "📊 STATISTIKA\n"
    report += "=" * 40 + "\n"

    # 1. Haftalik statistika
    weekly = get_weekly_stats()
    report += create_text_chart(weekly, "Hafta Kunlari", max_width=15)
    report += "\n" + "─" * 40 + "\n"  # Ajratuvchi chiziq

    # 2. Soatlik statistika (top 10)
    hourly = get_hourly_stats()
    report += create_text_chart(hourly, "TOP 10 Vaqtlar", max_width=15)
    report += "\n" + "─" * 40 + "\n"

    # 3. Maydon populyarligi
    fields = get_field_popularity()
    fields_formatted = [(f.capitalize(), c) for f, c in fields]
    report += create_text_chart(fields_formatted, "Maydonlar", max_width=15)
    report += "\n" + "─" * 40 + "\n"

    # 4. Haftalik daromad
    weekly_revenue = get_weekly_revenue()
    report += create_text_chart(weekly_revenue, "Haftalik (ming)", max_width=15)
    report += "\n" + "─" * 40 + "\n"

    # 5. Oylik trend
    monthly = get_monthly_trend()
    # Oy nomlarini qisqartirish (eng uzun: September = 9)
    monthly_short = [(m[:9], c) for m, c in monthly]
    report += create_text_chart(monthly_short, "6 Oylik Trend", max_width=15)

    return report


def generate_excel_report():
    """
    Professional Excel fayl - oylar bo'yicha tartibli
    Doimiy fayl, har doim yangilanadi
    """
    session = get_session()
    try:
        # Barcha bookinglarni olish, sana bo'yicha
        bookings = session.query(Booking).order_by(Booking.date.desc()).all()

        if not bookings:
            return "Ma'lumot yo'q".encode('utf-8-sig')

        # Oylar bo'yicha guruhlash
        from collections import defaultdict
        months_data = defaultdict(list)

        for b in bookings:
            # Oy nomi: "Oktabr-2025"
            month_key = b.date.strftime('%B-%Y')
            months_data[month_key].append(b)

        # CSV yaratish
        csv_content = ""

        # Har bir oy uchun
        for month_name in sorted(months_data.keys(), reverse=True):
            month_bookings = months_data[month_name]

            # Oy sarlavhasi
            csv_content += f"\n{month_name.upper()}\n"
            csv_content += "№,ID,F.I.SH,Sana,Vaqt,Maydon\n"

            # Bookinglar
            for idx, b in enumerate(month_bookings, 1):
                user = get_user_by_id(b.user_id)

                if user:
                    full_name = f"{user.surname} {user.name}"
                else:
                    full_name = "N/A"

                csv_content += f"{idx},"
                csv_content += f"{b.id},"
                csv_content += f"{full_name},"
                csv_content += f"{b.date.strftime('%d.%m.%Y')},"
                csv_content += f"{b.slot},"
                csv_content += f"{b.field}\n"

            csv_content += "\n"

        return csv_content.encode('utf-8-sig')

    finally:
        session.close()
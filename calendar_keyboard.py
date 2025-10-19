from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar
import datetime
from config import DAYS_OF_WEEK, MONTHS


def create_calendar(year=None, month=None):
    """
    Kalendar inline keyboard yaratish
    """
    now = datetime.datetime.now()
    if year is None: year = now.year
    if month is None: month = now.month

    markup = InlineKeyboardMarkup()

    # Header - Month and Year
    row = []
    row.append(InlineKeyboardButton(
        f"{MONTHS[month - 1]} {year}",
        callback_data="ignore"
    ))
    markup.row(*row)

    # Days of week header
    row = []
    for day in DAYS_OF_WEEK:
        row.append(InlineKeyboardButton(day, callback_data="ignore"))
    markup.row(*row)

    # Calendar days
    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                date = datetime.date(year, month, day)
                # O'tgan kunlarni disable qilish
                if date < datetime.date.today():
                    row.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"calendar_day_{year}_{month}_{day}"
                    ))
        markup.row(*row)

    # Navigation buttons
    row = []
    # Previous month
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    # Next month
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    row.append(InlineKeyboardButton(
        "◀️",
        callback_data=f"calendar_nav_{prev_year}_{prev_month}"
    ))
    row.append(InlineKeyboardButton(
        "❌ Bekor",
        callback_data="calendar_cancel"
    ))
    row.append(InlineKeyboardButton(
        "▶️",
        callback_data=f"calendar_nav_{next_year}_{next_month}"
    ))
    markup.row(*row)

    return markup


def separate_callback_data(data):
    """
    Callback data ni ajratish
    calendar_day_2025_10_15 -> (2025, 10, 15)
    """
    parts = data.split('_')
    if len(parts) >= 4:
        return int(parts[2]), int(parts[3]), int(parts[4])
    return None, None, None
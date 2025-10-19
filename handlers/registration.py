import re
from db import get_user, add_user
from utils import main_menu, request_contact


def register_handlers(bot, states):
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        user_id = message.from_user.id
        user = get_user(user_id)

        if user:
            bot.send_message(
                user_id,
                f"👋 Xush kelibsiz, {user.name}!\n\n"
                "Quyidagi menyudan tanlang:",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(
                user_id,
                "👋 Assalomu alaykum!\n\n"
                "Botdan foydalanish uchun ro'yxatdan o'ting.\n\n"
                "Iltimos, ismingizni kiriting:"
            )
            states[user_id] = {'step': 'waiting_name'}

    @bot.message_handler(commands=['register'])
    def cmd_register(message):
        user_id = message.from_user.id
        user = get_user(user_id)

        if user:
            bot.send_message(
                user_id,
                "✅ Siz allaqachon ro'yxatdan o'tgansiz!",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(user_id, "👤 Ismingizni kiriting:")
            states[user_id] = {'step': 'waiting_name'}

    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'waiting_name')
    def get_name(message):
        user_id = message.from_user.id
        name = message.text.strip()

        if len(name) < 2:
            bot.send_message(user_id, "❌ Ism juda qisqa. Qaytadan kiriting:")
            return

        states[user_id]['name'] = name
        states[user_id]['step'] = 'waiting_surname'
        bot.send_message(user_id, "👤 Familyangizni kiriting:")

    @bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get('step') == 'waiting_surname')
    def get_surname(message):
        user_id = message.from_user.id
        surname = message.text.strip()

        if len(surname) < 2:
            bot.send_message(user_id, "❌ Familya juda qisqa. Qaytadan kiriting:")
            return

        states[user_id]['surname'] = surname
        states[user_id]['step'] = 'waiting_phone'
        bot.send_message(
            user_id,
            "📱 Telefon raqamingizni ulashish uchun tugmani bosing:(Iltimos,faol raqamdagi hisobdan foydalaning!)",
            reply_markup=request_contact()
        )

    @bot.message_handler(
        content_types=['contact'],
        func=lambda m: states.get(m.from_user.id, {}).get('step') == 'waiting_phone'
    )
    def get_phone(message):
        user_id = message.from_user.id

        if not message.contact:
            bot.send_message(user_id, "❌ Raqam ulashilmadi. Qaytadan urinib ko'ring.")
            return

        phone = message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone

        # Validate phone
        if not re.match(r'^\+998\d{9}$', phone):
            bot.send_message(
                user_id,
                "❌ Faqat O'zbekiston raqamlari qabul qilinadi (+998...)\n"
                "Qaytadan urinib ko'ring:",
                reply_markup=request_contact()
            )
            return

        # Save user
        name = states[user_id]['name']
        surname = states[user_id]['surname']

        user = add_user(user_id, name, surname, phone)

        if user:
            bot.send_message(
                user_id,
                f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
                f"👤 {name} {surname}\n"
                f"📞 {phone}",
                reply_markup=main_menu()
            )
            del states[user_id]
        else:
            bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring: /register")

    @bot.message_handler(
        func=lambda m: states.get(m.from_user.id, {}).get('step') == 'waiting_phone'
                       and m.content_type != 'contact'
    )
    def invalid_phone_input(message):
        bot.send_message(
            message.from_user.id,
            "❌ Iltimos, '📱 Raqamni ulashish' tugmasini bosing!",
            reply_markup=request_contact()
        )
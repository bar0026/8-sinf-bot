import os
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = "8199437478:AAGYuqU0npc5tmkjEEMnPcSc3wqi4T0_ifo"  # <-- E'TIBOR BERING: bu yerda tokenni yangilang
bot = telebot.TeleBot(BOT_TOKEN)

REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@hamkor_informatiklar"},
    {"name": "2-kanal", "username": "@Matematika_6sinf_yechimi_2022"},
    {"name": "3-kanal", "username": "@algebra_7_sinf_yechimi_2022"},
    {"name": "4-kanal", "username": "@bsb_chsb_javoblari1"},
]

LINKS = {
    "bsb_5": "https://www.test-uz.ru/sor_uz.php?klass=5",
    "bsb_6": "https://www.test-uz.ru/sor_uz.php?klass=6",
    "bsb_7": "https://www.test-uz.ru/sor_uz.php?klass=7",
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "bsb_9": "https://www.test-uz.ru/sor_uz.php?klass=9",
    "bsb_10": "https://www.test-uz.ru/sor_uz.php?klass=10",
    "bsb_11": "https://www.test-uz.ru/sor_uz.php?klass=11",
    "chsb_5": "https://www.test-uz.ru/soch_uz.php?klass=5",
    "chsb_6": "https://www.test-uz.ru/soch_uz.php?klass=6",
    "chsb_7": "https://www.test-uz.ru/soch_uz.php?klass=7",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
    "chsb_9": "https://www.test-uz.ru/soch_uz.php?klass=9",
    "chsb_10": "https://www.test-uz.ru/soch_uz.php?klass=10",
    "chsb_11": "https://www.test-uz.ru/soch_uz.php?klass=11",
}

ADMIN_ID = 2051084228

# Foydalanuvchini saqlash
def save_user(user_id):
    try:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        users = []

    if str(user_id) not in users:
        users.append(str(user_id))
        with open("users.txt", "w") as f:
            f.write("\n".join(users))


# Obuna holatini tekshirish
def check_subscription_status(user_id):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(channel["name"])
        except Exception:
            not_subscribed.append(channel["name"])
    return not_subscribed


# Kanal obunasi uchun INLINE tugma (qoladi)
def subscription_buttons(not_subscribed=None):
    markup = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_subscribed is None else [c for c in REQUIRED_CHANNELS if c['name'] in not_subscribed]
    for channel in channels:
        markup.add(types.InlineKeyboardButton(channel['name'], url=f"https://t.me/{channel['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return markup


# Yangi funksiya: foydalanuvchi obunasini tekshiradi va agar to'liq emas bo'lsa, habar yuboradi va keyingi amalni to'xtatadi
def check_user_subscriptions(message_or_call):
    user_id = message_or_call.from_user.id
    chat_id = message_or_call.message.chat.id if hasattr(message_or_call, "message") else message_or_call.chat.id

    not_subscribed = check_subscription_status(user_id)
    if not_subscribed:
        msg = "❌ Siz quyidagi kanallarga obuna bo‘lmagansiz:\n"
        msg += "\n".join(f"• {name}" for name in not_subscribed)
        msg += "\n\nIltimos, obuna bo‘ling va keyin tekshirib ko‘ring."
        markup = subscription_buttons(not_subscribed)
        if hasattr(message_or_call, "message"):  # callback_query
            bot.answer_callback_query(message_or_call.id, "Obuna bo'lish kerak", show_alert=True)
            bot.edit_message_text(chat_id=chat_id, message_id=message_or_call.message.message_id, text=msg, reply_markup=markup)
        else:  # oddiy message
            bot.send_message(chat_id, msg, reply_markup=markup)
        return False
    return True


# Asosiy menyu tugmalari
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📚 BSB JAVOBLARI"),
        types.KeyboardButton("❗️ CHSB JAVOBLARI"),
        types.KeyboardButton("📬 Reklama xizmati")
    )
    return markup


def sub_menu_markup(data):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    grades = list(range(5, 12))
    # Tugmalarni juftlab joylashtirish
    for i in range(0, len(grades), 2):
        row_buttons = []
        for grade in grades[i:i+2]:
            text = f"{grade}-sinf BSB" if data == "bsb" else f"{grade}-sinf CHSB"
            row_buttons.append(types.KeyboardButton(text))
        markup.row(*row_buttons)
    markup.add(types.KeyboardButton("🏠 Asosiy menyu"))
    return markup


# /start komandasi
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    save_user(user_id)

    user_name = message.from_user.first_name
    welcome_text = f"""Assalomu alaykum {user_name} 👋🏻  
Botimizga xush kelibsiz 🎊

Bu bot orqali:
 • Bsb javobi va savoli
 • Chsb javobi va savoli
 • BSB CHSB uchun slayd va esselarni topishingiz mumkin hammasi tekin 🎁  

Botdan foydalanish uchun kanalga obuna boʻling va tekshirish tugmasini bosing ‼️"""

    markup = subscription_buttons()
    bot.send_message(chat_id=message.chat.id, text=welcome_text, reply_markup=markup)


# Obunani tekshirish tugmasi
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subscriptions(call):
    user_id = call.from_user.id
    not_subscribed = check_subscription_status(user_id)

    if not_subscribed:
        msg = "❌ Quyidagi kanallarga obuna bo‘lmagansiz:\n"
        msg += "\n".join(f"• {name}" for name in not_subscribed)
        msg += "\n\nIltimos, quyidagi kanallarga obuna bo‘ling va keyin tekshirib ko‘ring."
        markup = subscription_buttons(not_subscribed)
        bot.answer_callback_query(call.id, "Siz obuna emassiz", show_alert=True)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
    else:
        msg = "✅ Siz barcha kanallarga obuna bo‘lgansiz!\nEndi botdan foydalanishingiz mumkin 🎉"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg)
        bot.send_message(chat_id=call.message.chat.id, text="Asosiy menyu:", reply_markup=main_menu_markup())


# BSB menyu tugmasi
@bot.message_handler(func=lambda message: message.text == "📚 BSB JAVOBLARI")
def bsb_menu(message):
    if not check_user_subscriptions(message):
        return
    markup = sub_menu_markup("bsb")
    bot.send_message(message.chat.id, "BSB sinflarni tanlang:", reply_markup=markup)


# CHSB menyu tugmasi
@bot.message_handler(func=lambda message: message.text == "❗️ CHSB JAVOBLARI")
def chsb_menu(message):
    if not check_user_subscriptions(message):
        return
    markup = sub_menu_markup("chsb")
    bot.send_message(message.chat.id, "CHSB sinflarni tanlang:", reply_markup=markup)


# Reklama tugmasi
@bot.message_handler(func=lambda message: message.text == "📬 Reklama xizmati")
def reklama_menu(message):
    if not check_user_subscriptions(message):
        return
    bot.send_message(message.chat.id, "📬 Reklama uchun admin bilan bog‘laning: @BAR_xn")


# Asosiy menyuga qaytish
@bot.message_handler(func=lambda message: message.text == "🏠 Asosiy menyu")
def return_main_menu(message):
    if not check_user_subscriptions(message):
        return
    bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())


# Sinf tanlaganda link yuborish
@bot.message_handler(func=lambda message: any(x in message.text for x in ["BSB", "CHSB"]))
def grade_link_handler(message):
    if not check_user_subscriptions(message):
        return
    try:
        parts = message.text.split()
        grade = parts[0].replace("-sinf", "")
        typ = "bsb" if "BSB" in message.text else "chsb"
        key = f"{typ}_{grade}"
        link = LINKS.get(key)

        if link:
            bot.send_message(message.chat.id, f"Siz tanladingiz: {message.text}\nHavola: {link}")
        else:
            bot.send_message(message.chat.id, "Kechirasiz, ushbu sinf uchun havola topilmadi.")
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        bot.send_message(message.chat.id, "Xatolik yuz berdi.")


# /stats komandasi (admin uchun)
@bot.message_handler(commands=['stats'])
def stats_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Sizda bu buyruqni ishlatishga ruxsat yo'q.")
        return
    try:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        users = []
    bot.send_message(message.chat.id, f"Botni ishlatgan foydalanuvchilar soni: {len(users)}")


# Webhook uchun
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})


# Webhook sozlash
def set_webhook():
    webhook_url = f"https://8sinfbot.onrender.com/{BOT_TOKEN}"  # <-- Bu yerda domeningizni yozing
    bot.remove_webhook()
    result = bot.set_webhook(url=webhook_url)
    if result:
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.error("Webhook set failed")


# Flask serverni ishga tushirish
def main():
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

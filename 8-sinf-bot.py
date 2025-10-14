import os
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging

# === LOGGING ===
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# === FLASK APP ===
app = Flask(__name__)

# === BOT TOKEN ===
BOT_TOKEN = "8169442989:AAG6Zn2VBvx3VO1fU6lCv--gavT2N6235nM"  # bu joyga tokeningni qo‘y
bot = telebot.TeleBot(BOT_TOKEN)

# === KERAKLI KANALLAR ===
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},  
    {"name": "2-kanal", "username": "@hamkor_informatiklar"},

]

# === 8-sinf uchun linklar ===
LINKS = {
    "bsb": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "chsb": "https://www.test-uz.ru/soch_uz.php?klass=8",
}

# === Obuna tekshiruvi ===
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


def subscription_buttons(not_subscribed=None):
    markup = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_subscribed is None else [c for c in REQUIRED_CHANNELS if c['name'] in not_subscribed]
    for channel in channels:
        markup.add(types.InlineKeyboardButton(channel['name'], url=f"https://t.me/{channel['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return markup


# === Asosiy menyu (faqat 2 tugma) ===
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📚 8-sinf BSB"),
        types.KeyboardButton("❗️ 8-sinf CHSB")
    )
    return markup


# === START komandasi ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    not_subscribed = check_subscription_status(user_id)

    if not_subscribed:
        msg = "❌ Iltimos, quyidagi kanallarga obuna bo‘ling 👇"
        markup = subscription_buttons(not_subscribed)
        bot.send_message(message.chat.id, msg, reply_markup=markup)
    else:
        bot.send_message(
            message.chat.id,
            "✅ Obuna tekshirildi! Endi 8-sinf BSB yoki CHSB tanlang:",
            reply_markup=main_menu_markup()
        )


# === Callback: obunani qayta tekshirish ===
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs_callback(call):
    user_id = call.from_user.id
    not_subscribed = check_subscription_status(user_id)

    if not_subscribed:
        msg = "❌ Hali quyidagi kanallarga obuna bo‘lmadingiz:\n"
        msg += "\n".join(f"• {ch}" for ch in not_subscribed)
        markup = subscription_buttons(not_subscribed)
        bot.answer_callback_query(call.id, "Obuna kerak", show_alert=True)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ Obuna tasdiqlandi!")
        bot.send_message(call.message.chat.id, "Endi 8-sinf variantini tanlang 👇", reply_markup=main_menu_markup())


# === Tugma bosilganda link yuborish ===
@bot.message_handler(func=lambda message: message.text in ["BSB JAVOBLARI✅", "CHSB JAVOBLARI📎"])
def send_link(message):
    user_id = message.from_user.id
    not_subscribed = check_subscription_status(user_id)

    if not_subscribed:
        msg = "❌ Iltimos, quyidagi kanallarga obuna bo‘ling 👇"
        markup = subscription_buttons(not_subscribed)
        bot.send_message(message.chat.id, msg, reply_markup=markup)
        return

    if "BSB" in message.text:
        bot.send_message(message.chat.id, f"📘 8-sinf BSB javoblari: {LINKS['bsb']}")
    else:
        bot.send_message(message.chat.id, f"📗 8-sinf CHSB javoblari: {LINKS['chsb']}")


# === WEBHOOK yo‘lga qo‘yish ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})


def set_webhook():
    webhook_url = f"https://eightsinfbot.onrender.com/{BOT_TOKEN}"  # bu joyga Render domeningni yoz
    bot.remove_webhook()
    result = bot.set_webhook(url=webhook_url)
    if result:
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.error("Webhook set failed")


def main():
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

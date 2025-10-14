import os
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- BOT TOKEN ---
BOT_TOKEN = "8169442989:AAG6Zn2VBvx3VO1fU6lCv--gavT2N6235nM"  # <-- O'zingning tokeningni qo'y
bot = telebot.TeleBot(BOT_TOKEN)

# --- KERAKLI KANALLAR ---
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@hamkor_informatiklar"},
]

# --- LINKLAR ---
LINKS = {
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
}

# --- ADMIN ID ---
ADMIN_ID = 2051084228

# --- FOYDALANUVCHINI SAQLASH ---
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


# --- OBUNA HOLATINI TEKSHIRISH ---
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


# --- OBUNA TUGMALARI ---
def subscription_buttons(not_subscribed=None):
    markup = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_subscribed is None else [
        c for c in REQUIRED_CHANNELS if c['name'] in not_subscribed
    ]
    for channel in channels:
        markup.add(types.InlineKeyboardButton(channel['name'], url=f"https://t.me/{channel['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return markup


# --- OBUNANI TEKSHIRISH FUNKSIYASI ---
def check_user_subscriptions(message_or_call):
    user_id = message_or_call.from_user.id
    chat_id = message_or_call.message.chat.id if hasattr(message_or_call, "message") else message_or_call.chat.id

    not_subscribed = check_subscription_status(user_id)
    if not_subscribed:
        msg = "❌ Siz quyidagi kanallarga obuna bo‘lmagansiz:\n"
        msg += "\n".join(f"• {name}" for name in not_subscribed)
        msg += "\n\nIltimos, obuna bo‘ling va keyin tekshirib ko‘ring."
        markup = subscription_buttons(not_subscribed)
        if hasattr(message_or_call, "message"):
            bot.answer_callback_query(message_or_call.id, "Obuna bo'lish kerak", show_alert=True)
            bot.edit_message_text(chat_id=chat_id, message_id=message_or_call.message.message_id, text=msg, reply_markup=markup)
        else:
            bot.send_message(chat_id, msg, reply_markup=markup)
        return False
    return True


# --- ASOSIY MENYU ---
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📚 BSB JAVOBLARI"), types.KeyboardButton("❗️ CHSB JAVOBLARI"))
    markup.add(types.KeyboardButton("📬 Reklama xizmati"))
    return markup


# --- /start ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    save_user(user_id)
    user_name = message.from_user.first_name

    welcome = f"""👋 Salom {user_name}!
Botimizga xush kelibsiz 🎉  

Bu bot **faqat 8-sinf uchun** mo‘ljallangan.

📚 BSB va ❗️ CHSB javoblarini olish uchun, quyidagi kanallarga obuna bo‘ling va “Tekshirish” tugmasini bosing ⬇️"""
    bot.send_message(message.chat.id, welcome, reply_markup=subscription_buttons())


# --- OBUNANI TEKSHIRISH CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs(call):
    user_id = call.from_user.id
    not_subscribed = check_subscription_status(user_id)
    if not_subscribed:
        msg = "❌ Quyidagi kanallarga obuna bo‘lmagansiz:\n"
        msg += "\n".join(f"• {name}" for name in not_subscribed)
        markup = subscription_buttons(not_subscribed)
        bot.answer_callback_query(call.id, "Obuna emassiz", show_alert=True)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "Obuna tekshirildi ✅")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="✅ Siz barcha kanallarga obuna bo‘lgansiz!\nEndi botdan foydalanishingiz mumkin 🎉")
        bot.send_message(call.message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())


# --- BSB 8-sinf ---
@bot.message_handler(func=lambda m: m.text == "📚 BSB JAVOBLARI")
def bsb_handler(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id, f"📚 8-sinf BSB javoblari:\n{LINKS['bsb_8']}")


# --- CHSB 8-sinf ---
@bot.message_handler(func=lambda m: m.text == "❗️ CHSB JAVOBLARI")
def chsb_handler(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id, f"❗️ 8-sinf CHSB javoblari:\n{LINKS['chsb_8']}")


# --- Reklama tugmasi ---
@bot.message_handler(func=lambda m: m.text == "📬 Reklama xizmati")
def reklama_handler(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id, "📬 Reklama uchun admin bilan bog‘laning: @BAR_xn")


# --- /stats (admin uchun) ---
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Sizda ruxsat yo‘q ❌")
        return
    try:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        users = []
    bot.send_message(message.chat.id, f"👥 Umumiy foydalanuvchilar: {len(users)}")


# --- WEBHOOK ROUTE ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})


# --- WEBHOOK O‘RNATISH ---
def set_webhook():
    webhook_url = f"https://8sinfbot.onrender.com/{BOT_TOKEN}"  # domeningni o'zgartir
    bot.remove_webhook()
    result = bot.set_webhook(url=webhook_url)
    if result:
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.error("Webhook o‘rnatilmadi")


# --- MAIN FUNKSIYA ---
def main():
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Server {port}-portda ishga tushdi")
    try:
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Serverda xato: {e}")


if __name__ == "__main__":
    main()

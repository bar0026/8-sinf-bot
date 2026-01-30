import os
import logging
from datetime import datetime

from flask import Flask, request, jsonify
import telebot
from telebot import types
from pymongo import MongoClient

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)

# ======================
# FLASK
# ======================
app = Flask(__name__)

# ======================
# BOT
# ======================
BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html")

# ======================
# ADMIN
# ======================
ADMIN_ID = 2051084228

# ======================
# MONGODB
# ======================
MONGO_URI = "mongodb+srv://bar2606:asilbek0026-sinf-bot.yxrsvne.mongodb.net/?appName=8-sinf-bot"

try:
    client = MongoClient(MONGO_URI)
    client.admin.command("ping")
    db = client["telegram_bot"]
    users_col = db["users"]
    logging.info("MongoDB connected")
except Exception as e:
    logging.error(e)
    users_col = None

# ======================
# CHANNELS
# ======================
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@bsb_chsb_8_sinf_uchun"},
    {"name": "3-kanal", "username": "@chsb_original"},
    {"name": "4-kanal", "username": "@kulishamiz_keling"},
]

LINKS = {
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
}

# ======================
# DATABASE
# ======================
def save_user(uid, name):
    if not users_col:
        return
    users_col.update_one(
        {"user_id": uid},
        {"$setOnInsert": {
            "user_id": uid,
            "first_name": name,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "msg_count": 0
        }},
        upsert=True
    )

def inc_msg(uid):
    if users_col:
        users_col.update_one({"user_id": uid}, {"$inc": {"msg_count": 1}})

def get_users():
    if not users_col:
        return []
    return [u["user_id"] for u in users_col.find({}, {"user_id": 1})]

# ======================
# SUB CHECK
# ======================
def check_sub(uid):
    not_sub = []
    for ch in REQUIRED_CHANNELS:
        try:
            m = bot.get_chat_member(ch["username"], uid)
            if m.status not in ["member", "administrator", "creator"]:
                not_sub.append(ch["name"])
        except:
            not_sub.append(ch["name"])
    return not_sub

def sub_buttons(not_sub=None):
    kb = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_sub is None else [
        c for c in REQUIRED_CHANNELS if c["name"] in not_sub
    ]
    for ch in channels:
        kb.add(types.InlineKeyboardButton(
            ch["name"],
            url=f"https://t.me/{ch['username'][1:]}"
        ))
    kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return kb

def check_user(obj):
    uid = obj.from_user.id
    cid = obj.message.chat.id if hasattr(obj, "message") else obj.chat.id

    not_sub = check_sub(uid)
    if not_sub:
        text = "❌ Avval obuna bo‘ling:\n" + "\n".join(not_sub)
        if hasattr(obj, "message"):
            bot.answer_callback_query(obj.id, "Obuna bo‘ling!", show_alert=True)
            bot.edit_message_text(text, cid, obj.message.message_id, reply_markup=sub_buttons(not_sub))
        else:
            bot.send_message(cid, text, reply_markup=sub_buttons(not_sub))
        return False
    return True

# ======================
# MENUS
# ======================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("BSB JAVOBLARI✅", "CHSB JAVOBLARI📎")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👥 Foydalanuvchilar soni")
    kb.add("📢 Xabar yuborish")
    kb.add("⬅️ Ortga")
    return kb

# ======================
# HANDLERS
# ======================
@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "📚 Avval kanallarga obuna bo‘ling:",
        reply_markup=sub_buttons()
    )

@bot.callback_query_handler(func=lambda c: c.data == "check_subs")
def checksubs(call):
    save_user(call.from_user.id, call.from_user.first_name)
    inc_msg(call.from_user.id)
    if check_user(call):
        bot.send_message(call.message.chat.id, "✅ Tasdiqlandi!", reply_markup=main_menu())

@bot.message_handler(commands=["admin"])
def admin(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Siz admin emassiz!")
        return
    bot.send_message(message.chat.id, "🔐 Admin panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar soni")
def users_count(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    count = users_col.count_documents({}) if users_col else 0
    bot.send_message(message.chat.id, f"👥 Jami foydalanuvchilar: <b>{count}</b>")

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")
def ask_broadcast(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "✍️ Yuboriladigan xabarni kiriting:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        return
    sent = 0
    for uid in get_users():
        try:
            bot.send_message(uid, message.text)
            sent += 1
        except:
            pass
    bot.send_message(
        message.chat.id,
        f"✅ Xabar yuborildi\n📤 Yuborildi: {sent}",
        reply_markup=admin_menu()
    )

@bot.message_handler(func=lambda m: m.text == "⬅️ Ortga")
def back(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "BSB JAVOBLARI✅")
def bsb(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if check_user(message):
        bot.send_message(message.chat.id, LINKS["bsb_8"])

@bot.message_handler(func=lambda m: m.text == "CHSB JAVOBLARI📎")
def chsb(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)
    if check_user(message):
        bot.send_message(message.chat.id, LINKS["chsb_8"])

@bot.message_handler(content_types=["text"])
def counter(message):
    save_user(message.from_user.id, message.from_user.first_name)
    inc_msg(message.from_user.id)

# ======================
# WEBHOOK
# ======================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode())
    bot.process_new_updates([update])
    return jsonify(ok=True)

def set_webhook():
    url = "https://eight-sinf-bot.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{url}/{BOT_TOKEN}")
    logging.info("Webhook set")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging
from datetime import datetime
from pymongo import MongoClient

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- TOKEN ---
BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html")

# --- ADMIN ---
ADMIN_ID = 2051084228

# --- MONGODB ---
MONGO_URI = "mongodb+srv://bar2606:Parol123@8-sinf-bot.yxrsvne.mongodb.net/?appName=8-sinf-bot"

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    logging.info("MongoDB connected successfully")
    db = client["telegram_bot"]
    users_col = db["users"]
except Exception as e:
    logging.error(f"MongoDB connection failed: {e}")
    db = None
    users_col = None

# --- CHANNELS ---
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

def save_user(user_id, first_name):
    if not users_col:
        logging.warning("Database not connected, skipping save_user")
        return
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        users_col.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "user_id": user_id,
                "first_name": first_name,
                "joined": today,
                "msg_count": 0
            }},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error saving user {user_id}: {e}")

def increase_message_count(user_id):
    if not users_col:
        logging.warning("Database not connected, skipping increase_message_count")
        return
    
    try:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"msg_count": 1}}
        )
    except Exception as e:
        logging.error(f"Error increasing message count for {user_id}: {e}")

def get_all_users():
    if not users_col:
        logging.warning("Database not connected, returning empty list")
        return []
    
    try:
        return [u["user_id"] for u in users_col.find({}, {"user_id":1})]
    except Exception as e:
        logging.error(f"Error getting all users: {e}")
        return []

def get_all_full():
    if not users_col:
        logging.warning("Database not connected, returning empty list")
        return []
    
    try:
        return list(users_col.find())
    except Exception as e:
        logging.error(f"Error getting all users data: {e}")
        return []

# ======================
# SUB CHECK
# ======================

def check_subscription_status(user_id):
    not_sub = []
    for ch in REQUIRED_CHANNELS:
        try:
            m = bot.get_chat_member(ch["username"], user_id)
            if m.status not in ["member","administrator","creator"]:
                not_sub.append(ch["name"])
        except:
            not_sub.append(ch["name"])
    return not_sub

def subscription_buttons(not_sub=None):
    m = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_sub is None else \
        [c for c in REQUIRED_CHANNELS if c["name"] in not_sub]

    for ch in channels:
        m.add(types.InlineKeyboardButton(
            ch["name"],
            url=f"https://t.me/{ch['username'][1:]}"
        ))

    m.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return m

def check_user_subscriptions(obj):
    uid = obj.from_user.id
    chat_id = obj.message.chat.id if hasattr(obj,"message") else obj.chat.id

    not_sub = check_subscription_status(uid)

    if not_sub:
        msg = "❌ Avval obuna bo'ling:\n" + "\n".join(not_sub)
        markup = subscription_buttons(not_sub)

        if hasattr(obj,"message"):
            bot.answer_callback_query(obj.id,"Obuna bo'ling!",show_alert=True)
            bot.edit_message_text(msg,chat_id,obj.message.message_id,reply_markup=markup)
        else:
            bot.send_message(chat_id,msg,reply_markup=markup)
        return False
    return True

# ======================
# MENU
# ======================

def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("BSB JAVOBLARI✅","CHSB JAVOBLARI📎")
    return m

# ======================
# HANDLERS
# ======================

@bot.message_handler(commands=['start'])
def start_handler(message):
    save_user(message.from_user.id,message.from_user.first_name)
    bot.send_message(
        message.chat.id,
        "📚 Avval kanallarga obuna bo'ling:",
        reply_markup=subscription_buttons()
    )

@bot.callback_query_handler(func=lambda c:c.data=="check_subs")
def check_subs(call):
    if check_user_subscriptions(call):
        bot.send_message(call.message.chat.id,"✅ Tasdiqlandi!",reply_markup=main_menu())

@bot.message_handler(func=lambda m:m.text=="BSB JAVOBLARI✅")
def bsb(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id,LINKS["bsb_8"])

@bot.message_handler(func=lambda m:m.text=="CHSB JAVOBLARI📎")
def chsb(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id,LINKS["chsb_8"])

# ======================
# BROADCAST
# ======================

def broadcast_message(text):
    users = get_all_users()
    for uid in users:
        try:
            bot.send_message(uid,text)
        except:
            pass

# ======================
# MESSAGE COUNTER
# ======================

@bot.message_handler(content_types=['text'])
def counter(message):
    if not message.text.startswith("/"):
        save_user(message.from_user.id,message.from_user.first_name)
        increase_message_count(message.from_user.id)

# ======================
# WEBHOOK
# ======================

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return jsonify({"ok": True})

def set_webhook():
    render_url = "https://eight-sinf-bot.onrender.com"
    
    try:
        bot.remove_webhook()
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logging.error(f"Webhook error: {e}")

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
        today = datetime.now().strftime("%Y-%m-%d")
        users_col.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "user_id": user_id,
                "first_name": first_name,
                "joined": today,
                "msg_count": 0
            }},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error saving user {user_id}: {e}")

def increase_message_count(user_id):
    if not users_col:
        logging.warning("Database not connected, skipping increase_message_count")
        return
    
    try:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"msg_count": 1}}
        )
    except Exception as e:
        logging.error(f"Error increasing message count for {user_id}: {e}")

def get_all_users():
    if not users_col:
        logging.warning("Database not connected, returning empty list")
        return []
    
    try:
        return [u["user_id"] for u in users_col.find({}, {"user_id":1})]
    except Exception as e:
        logging.error(f"Error getting all users: {e}")
        return []

def get_all_full():
    if not users_col:
        logging.warning("Database not connected, returning empty list")
        return []
    
    try:
        return list(users_col.find())
    except Exception as e:
        logging.error(f"Error getting all users data: {e}")
        return []

# ======================
# SUB CHECK
# ======================

def check_subscription_status(user_id):
    not_sub = []
    for ch in REQUIRED_CHANNELS:
        try:
            m = bot.get_chat_member(ch["username"], user_id)
            if m.status not in ["member","administrator","creator"]:
                not_sub.append(ch["name"])
        except:
            not_sub.append(ch["name"])
    return not_sub

def subscription_buttons(not_sub=None):
    m = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_sub is None else \
        [c for c in REQUIRED_CHANNELS if c["name"] in not_sub]

    for ch in channels:
        m.add(types.InlineKeyboardButton(
            ch["name"],
            url=f"https://t.me/{ch['username'][1:]}"
        ))

    m.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return m

def check_user_subscriptions(obj):
    uid = obj.from_user.id
    chat_id = obj.message.chat.id if hasattr(obj,"message") else obj.chat.id

    not_sub = check_subscription_status(uid)

    if not_sub:
        msg = "❌ Avval obuna bo‘ling:\n" + "\n".join(not_sub)
        markup = subscription_buttons(not_sub)

        if hasattr(obj,"message"):
            bot.answer_callback_query(obj.id,"Obuna bo‘ling!",show_alert=True)
            bot.edit_message_text(msg,chat_id,obj.message.message_id,reply_markup=markup)
        else:
            bot.send_message(chat_id,msg,reply_markup=markup)
        return False
    return True

# ======================
# MENU
# ======================

def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("BSB JAVOBLARI✅","CHSB JAVOBLARI📎")
    return m

# ======================
# HANDLERS
# ======================

@bot.message_handler(commands=['start'])
def start_handler(message):
    save_user(message.from_user.id,message.from_user.first_name)
    bot.send_message(
        message.chat.id,
        "📚 Avval kanallarga obuna bo‘ling:",
        reply_markup=subscription_buttons()
    )

@bot.callback_query_handler(func=lambda c:c.data=="check_subs")
def check_subs(call):
    if check_user_subscriptions(call):
        bot.send_message(call.message.chat.id,"✅ Tasdiqlandi!",reply_markup=main_menu())

@bot.message_handler(func=lambda m:m.text=="BSB JAVOBLARI✅")
def bsb(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id,LINKS["bsb_8"])

@bot.message_handler(func=lambda m:m.text=="CHSB JAVOBLARI📎")
def chsb(message):
    if not check_user_subscriptions(message): return
    bot.send_message(message.chat.id,LINKS["chsb_8"])

# ======================
# BROADCAST
# ======================

def broadcast_message(text):
    users = get_all_users()
    for uid in users:
        try:
            bot.send_message(uid,text)
        except:
            pass

# ======================
# MESSAGE COUNTER
# ======================

@bot.message_handler(content_types=['text'])
def counter(message):
    if not message.text.startswith("/"):
        save_user(message.from_user.id,message.from_user.first_name)
        increase_message_count(message.from_user.id)

# ======================
# WEBHOOK
# ======================

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return jsonify({"ok": True})

def set_webhook():
    render_url = "https://eight-sinf-bot.onrender.com"
    
    try:
        bot.remove_webhook()
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logging.error(f"Webhook error: {e}")

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


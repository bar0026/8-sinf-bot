import os

from flask import Flask, request, jsonify

import telebot

from telebot import types

import logging

from datetime import datetime

import sqlite3

import threading

import time

--- LOGGING ---

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(name)

app = Flask(name)

--- BOT TOKEN ---

BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"

bot = telebot.TeleBot(BOT_TOKEN)

--- ADMIN ID ---

ADMIN_ID = 2051084228

--- REQUIRED CHANNELS ---

REQUIRED_CHANNELS = [

{"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},

{"name": "2-kanal", "username": "@bsb_chsb_8_sinf_uchun"},

{"name": "3-kanal", "username": "@chsb_original"},

{"name": "4-kanal", "username": "@kulishamiz_keling"},

]

--- LINKS ---

LINKS = {

"bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",

"chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",

}

===============================

DATABASE FUNCTIONS

===============================

def init_db():

conn = sqlite3.connect("users.db")

c = conn.cursor()

c.execute("""

    CREATE TABLE IF NOT EXISTS users(

        user_id INTEGER PRIMARY KEY,

        first_name TEXT,

        joined TEXT,

        msg_count INTEGER

    )

""")

conn.commit()

conn.close()

def save_user(user_id, first_name):

conn = sqlite3.connect("users.db")

c = conn.cursor()

today = datetime.now().strftime("%Y-%m-%d")

c.execute("INSERT OR IGNORE INTO users(user_id, first_name, joined, msg_count) VALUES (?, ?, ?, 0)",

          (user_id, first_name, today))

conn.commit()

conn.close()

def increase_message_count(user_id):

conn = sqlite3.connect("users.db")

c = conn.cursor()

c.execute("UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?", (user_id,))

conn.commit()

conn.close()

def get_all_users():

conn = sqlite3.connect("users.db")

c = conn.cursor()

c.execute("SELECT user_id FROM users")

users = [row[0] for row in c.fetchall()]

conn.close()

return users

def get_all_full():

conn = sqlite3.connect("users.db")

c = conn.cursor()

c.execute("SELECT * FROM users")

users = c.fetchall()

conn.close()

return users

===============================

SUBSCRIPTION CHECK

===============================

def check_subscription_status(user_id):

not_subscribed = []

for channel in REQUIRED_CHANNELS:

    try:

        member = bot.get_chat_member(channel["username"], user_id)

        if member.status not in ["member", "administrator", "creator"]:

            not_subscribed.append(channel["name"])

    except:

        not_subscribed.append(channel["name"])

return not_subscribed

def subscription_buttons(not_subscribed=None):

markup = types.InlineKeyboardMarkup()

channels = REQUIRED_CHANNELS if not_subscribed is None else [c for c in REQUIRED_CHANNELS if c["name"] in not_subscribed]

for channel in channels:

    markup.add(types.InlineKeyboardButton(channel["name"], url=f"https://t.me/{channel['username'][1:]}"))

markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))

return markup

def check_user_subscriptions(obj):

user_id = obj.from_user.id

chat_id = obj.message.chat.id if hasattr(obj, "message") else obj.chat.id



not_sub = check_subscription_status(user_id)

if not_sub:

    msg = "❌ Siz quyidagi kanallarga obuna emassiz:\n" + "\n".join(f"• {c}" for c in not_sub)

    markup = subscription_buttons(not_sub)

    if hasattr(obj, "message"):

        bot.answer_callback_query(obj.id, "Avval obuna bo‘ling!", show_alert=True)

        bot.edit_message_text(chat_id=chat_id, message_id=obj.message.message_id, text=msg, reply_markup=markup)

    else:

        bot.send_message(chat_id, msg, reply_markup=markup)

    return False

return True

===============================

MENUS

===============================

def main_menu():

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

markup.add("BSB JAVOBLARI✅", "CHSB JAVOBLARI📎")

return markup

def admin_panel_markup():

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

markup.add("📢 Xabar yuborish", "📊 Statistika")

markup.add("🔕 Broadcasting bekor qilish", "🏠 Bosh menyu")

return markup

===============================

HANDLERS

===============================

@bot.message_handler(commands=['start'])

def start_handler(message):

save_user(message.from_user.id, message.from_user.first_name)

text = f"👋 Salom {message.from_user.first_name}!\nBotga xush kelibsiz!\n\n" \

       f"📚 BSB va CHSB javoblari uchun avval kanallarga obuna bo‘ling ⬇️"

bot.send_message(message.chat.id, text, reply_markup=subscription_buttons())

@bot.message_handler(commands=['admin'])

def admin_panel(message):

if message.from_user.id != ADMIN_ID:

    return bot.send_message(message.chat.id, "❌ Siz admin emassiz.")

bot.send_message(message.chat.id, "🔐 Admin panel:", reply_markup=admin_panel_markup())

@bot.callback_query_handler(func=lambda c: c.data == "check_subs")

def check_subs(call):

if check_user_subscriptions(call):

    bot.edit_message_text(

        chat_id=call.message.chat.id,

        message_id=call.message.message_id,

        text="✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin."

    )

    bot.send_message(call.message.chat.id, "Asosiy menyu:", reply_markup=main_menu())

--- BSB handler ---

@bot.message_handler(func=lambda m: m.text == "BSB JAVOBLARI✅")

def bsb_handler(message):

if not check_user_subscriptions(message): return

save_user(message.from_user.id, message.from_user.first_name)

bot.send_message(message.chat.id, f"📚 8-sinf BSB javoblari:\n{LINKS['bsb_8']}")

--- CHSB handler ---

@bot.message_handler(func=lambda m: m.text == "CHSB JAVOBLARI📎")

def chsb_handler(message):

if not check_user_subscriptions(message): return

save_user(message.from_user.id, message.from_user.first_name)

bot.send_message(message.chat.id, f"📎 8-sinf CHSB javoblari:\n{LINKS['chsb_8']}")

--- BROADCAST ---

broadcast_running = False

broadcast_cancelled = False

def broadcast_message(text):

global broadcast_running, broadcast_cancelled

broadcast_running = True

broadcast_cancelled = False



users = get_all_users()

total = len(users)

sent = 0



for i, user_id in enumerate(users):

    if broadcast_cancelled:

        bot.send_message(ADMIN_ID, "❌ Broadcasting bekor qilindi.")

        break

    try:

        bot.send_message(user_id, text)

        sent += 1

    except:

        pass



    if (i+1) % 100 == 0:

        bot.send_message(ADMIN_ID, f"📊 {i+1}/{total} yuborildi")



broadcast_running = False

bot.send_message(ADMIN_ID, f"✅ Tugadi! Yuborilgan: {sent}/{total}")

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")

def ask_text(message):

if message.from_user.id != ADMIN_ID: return

msg = bot.send_message(message.chat.id, "📢 Xabaringizni yuboring:")

bot.register_next_step_handler(msg, lambda m: threading.Thread(target=broadcast_message, args=(m.text,)).start())

@bot.message_handler(func=lambda m: m.text == "🔕 Broadcasting bekor qilish")

def cancel_broadcast_handler(message):

if message.from_user.id != ADMIN_ID: return

global broadcast_cancelled

broadcast_cancelled = True

bot.send_message(message.chat.id, "❌ Bekor qilindi.")

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh menyu")

def admin_back_to_main(message):

if message.from_user.id != ADMIN_ID: return

bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu())

--- STATISTICS ---

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")

def stats_handler(message):

if message.from_user.id != ADMIN_ID: return



users = get_all_full()

total = len(users)

today = datetime.now().strftime("%Y-%m-%d")

today_new = len([u for u in users if u[2] == today])



top_users = sorted(users, key=lambda x: x[3], reverse=True)[:10]

top_list = "\n".join([f"{i+1}. {u[1]} — {u[3]} ta xabar" for i, u in enumerate(top_users)]) or "Ma'lumot yo‘q"



bot.send_message(message.chat.id,

    f"📊 <b>Statistika:</b>\n"

    f"👥 Jami foydalanuvchilar: {total}\n"

    f"🆕 Bugun qo‘shilganlar: {today_new}\n\n"

    f"🔥 Eng faol foydalanuvchilar:\n{top_list}",

    parse_mode="HTML"

)

--- MESSAGE COUNTER (FAOLIYATNI HISOBLAYDI FAOL FOYDALANUVCHI XABARLARI ORQALI) ---

@bot.message_handler(content_types=['text'])

def message_counter(message):

if not message.text.startswith("/"):

    save_user(message.from_user.id, message.from_user.first_name)

    increase_message_count(message.from_user.id)

--- WEBHOOK ---

@app.route(f"/{BOT_TOKEN}", methods=["POST"])

def webhook():

update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))

bot.process_new_updates([update])

return jsonify({"ok": True})

def set_webhook():

bot.remove_webhook()

bot.set_webhook(url=f"https://eight-sinf-bot.onrender.com/{BOT_TOKEN}")

--- MAIN ---

if name == "main":

init_db()

set_webhook()

port = int(os.environ.get("PORT", 5000))

app.run(host="0.0.0.0", port=port)

import os
import time
import threading
import sqlite3
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 2051084228

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            msg_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id, first_name="NoName"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id, first_name, msg_count) VALUES(?, ?, 0)",
              (user_id, first_name))
    conn.commit()
    conn.close()

def increase_msg_count(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, msg_count FROM users")
    users = c.fetchall()  # [(id, name, msg_count), ...]
    conn.close()
    return users
# --------------------------------------------------

# Majburiy obuna kanallari
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@chsb_original"},
    {"name": "3-kanal", "username": "@kulishamiz_keling"},
]

# Linklar bazasi
LINKS = {
    "bsb_5": "https://www.test-uz.ru/sor_uz.php?klass=5 ",
    "bsb_6": "https://www.test-uz.ru/sor_uz.php?klass=6 ",
    "bsb_7": "https://www.test-uz.ru/sor_uz.php?klass=7 ",
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8 ",
    "bsb_9": "https://www.test-uz.ru/sor_uz.php?klass=9 ",
    "bsb_10": "https://www.test-uz.ru/sor_uz.php?klass=10 ",
    "bsb_11": "https://www.test-uz.ru/sor_uz.php?klass=11 ",
    "chsb_5": "https://www.test-uz.ru/soch_uz.php?klass=5 ",
    "chsb_6": "https://www.test-uz.ru/soch_uz.php?klass=6 ",
    "chsb_7": "https://www.test-uz.ru/soch_uz.php?klass=7 ",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8 ",
    "chsb_9": "https://www.test-uz.ru/soch_uz.php?klass=9 ",
    "chsb_10": "https://www.test-uz.ru/soch_uz.php?klass=10 ",
    "chsb_11": "https://www.test-uz.ru/soch_uz.php?klass=11 ",
}

# Obuna tekshirish
def check_subscription_status(user_id):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(channel["name"])
        except:
            not_subscribed.append(channel["name"])
    return not_subscribed

def subscription_buttons(not_subscribed=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    channels = REQUIRED_CHANNELS if not_subscribed is None else [c for c in REQUIRED_CHANNELS if c['name'] in not_subscribed]
    for channel in channels:
        markup.add(types.InlineKeyboardButton(channel['name'], url=f"https://t.me/ {channel['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return markup

# Admin panel tugmalari
def admin_panel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Statistika"),
        types.KeyboardButton("📣 Xabar yuborish (Hammaga)"),
        types.KeyboardButton("👤 Foydalanuvchiga xabar"),
        types.KeyboardButton("🔙 Chiqish")
    )
    return markup

# Asosiy menyu
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📚 BSB JAVOBLARI"),
        types.KeyboardButton("❗️ CHSB JAVOBLARI"),
        types.KeyboardButton("📬 Reklama xizmati")
    )
    return markup

# Sinf tanlash menyusi
def sub_menu_markup(data):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for i in range(5, 12, 2):
        row = []
        for grade in range(i, min(i + 2, 12)):
            txt = f"{grade}-sinf BSB" if data == "bsb" else f"{grade}-sinf CHSB"
            row.append(types.KeyboardButton(txt))
        markup.row(*row)
    markup.add(types.KeyboardButton("🏠 Asosiy menyu"))
    return markup

user_states = {}

# START
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    save_user(user_id, message.from_user.first_name)
    increase_msg_count(user_id)

    welcome = f"""Assalomu alaykum {message.from_user.first_name} 👋🏻
Botimizga xush kelibsiz 🎊

Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling 👇"""
    bot.send_message(message.chat.id, welcome, reply_markup=subscription_buttons())

# Obuna tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subscriptions(call):
    user_id = call.from_user.id
    save_user(user_id, call.from_user.first_name)
    increase_msg_count(user_id)

    not_sub = check_subscription_status(user_id)
    if not_sub:
        msg = "❌ Quyidagi kanallarga obuna emassiz:\n" + "\n".join(f"• {x}" for x in not_sub)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=subscription_buttons(not_sub))
        bot.answer_callback_query(call.id, "Obuna kerak!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Tasdiqlandi!")
        bot.edit_message_text("✅ Obuna tasdiqlandi!", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())

# Menyular
@bot.message_handler(func=lambda m: m.text in ["📚 BSB JAVOBLARI", "❗️ CHSB JAVOBLARI", "📬 Reklama xizmati", "🏠 Asosiy menyu"])
def menu_handler(message):
    user_id = message.from_user.id
    save_user(user_id, message.from_user.first_name)
    increase_msg_count(user_id)

    if message.text == "📚 BSB JAVOBLARI":
        bot.send_message(message.chat.id, "BSB sinfni tanlang:", reply_markup=sub_menu_markup("bsb"))
    elif message.text == "❗️ CHSB JAVOBLARI":
        bot.send_message(message.chat.id, "CHSB sinfni tanlang:", reply_markup=sub_menu_markup("chsb"))
    elif message.text == "📬 Reklama xizmati":
        bot.send_message(message.chat.id, "📬 Reklama uchun: @BAR_xn")
    elif message.text == "🏠 Asosiy menyu":
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())

# Sinf tanlash
@bot.message_handler(func=lambda m: any(f"{i}-sinf" in m.text for i in range(5, 12)))
def grade_handler(message):
    user_id = message.from_user.id
    save_user(user_id, message.from_user.first_name)
    increase_msg_count(user_id)

    try:
        grade = message.text.split("-")[0]
        typ = "bsb" if "BSB" in message.text else "chsb"
        key = f"{typ}_{grade}"
        link = LINKS.get(key)
        if link:
            bot.send_message(message.chat.id, f"🔗 {message.text}\nLink: {link}", reply_markup=main_menu_markup())
        else:
            bot.send_message(message.chat.id, "Bu sinf uchun link topilmadi.")
    except:
        bot.send_message(message.chat.id, "Xatolik yuz berdi.")

# ADMIN PANEL
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
    save_user(message.from_user.id, message.from_user.first_name)
    increase_msg_count(message.from_user.id)
    bot.send_message(message.chat.id, "🔐 Admin panel", reply_markup=admin_panel_markup())

@bot.message_handler(func=lambda m: m.text == "🔙 Chiqish" and m.from_user.id == ADMIN_ID)
def admin_exit(message):
    bot.send_message(message.chat.id, "Admin paneldan chiqdingiz.", reply_markup=main_menu_markup())

# Statistika
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def admin_stats(message):
    users = get_all_users()
    total = len(users)

    # eng faol 10 foydalanuvchi
    top_users = sorted(users, key=lambda x: x[2], reverse=True)[:10]
    top_list = "\n".join([f"{i+1}. {u[1]} — {u[2]} ta xabar" for i, u in enumerate(top_users)]) or "Ma'lumot yo‘q"

    bot.send_message(message.chat.id, f"📊 Foydalanuvchilar soni: {total} ta\n\n🔥 Eng faol foydalanuvchilar:\n{top_list}")

# Hammaga xabar
@bot.message_handler(func=lambda m: m.text == "📣 Xabar yuborish (Hammaga)" and m.from_user.id == ADMIN_ID)
def broadcast_all_start(message):
    bot.send_message(message.chat.id, "📩 Hammaga yuboriladigan xabarni yuboring.")
    user_states[message.from_user.id] = {"action": "broadcast_all"}

# Bitta odamga
@bot.message_handler(func=lambda m: m.text == "👤 Foydalanuvchiga xabar" and m.from_user.id == ADMIN_ID)
def broadcast_one_start(message):
    bot.send_message(message.chat.id, "Foydalanuvchi ID sining yuboring:")
    user_states[message.from_user.id] = {"action": "waiting_id"}

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'animation'])
def handle_broadcast(message):
    user_id = message.from_user.id
    save_user(user_id, message.from_user.first_name)
    increase_msg_count(user_id)

    if message.from_user.id != ADMIN_ID:
        return

    state = user_states.get(message.from_user.id)
    if not state:
        return

    if state["action"] == "waiting_id":
        try:
            target = int(message.text)
            user_states[message.from_user.id] = {"action": "broadcast_one", "target": target}
            bot.send_message(message.chat.id, "Endi yuboriladigan xabarni yuboring:")
        except:
            bot.send_message(message.chat.id, "Noto‘g‘ri ID. Raqam yozing.")
        return

    def send_messages():
        if state["action"] == "broadcast_all":
            users_list = get_all_users()
            users = [uid for uid, _, _ in users_list]
        else:
            users = [state["target"]]

        ok = 0
        for uid in users:
            try:
                if message.content_type == "text":
                    bot.send_message(uid, message.text)
                elif message.content_type == "photo":
                    bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
                ok += 1
            except:
                pass
            time.sleep(0.05)

        bot.send_message(message.chat.id, f"Yuborildi: {ok} ta")
        user_states.pop(message.from_user.id, None)

    threading.Thread(target=send_messages).start()

# Webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})

def set_webhook():
    url = f"https://eight-sinf-bot.onrender.com/ {BOT_TOKEN}"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=url)
    logger.info("Webhook o‘rnatildi!")

def main():
    init_db()
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()

import os
from flask import Flask, request, jsonify
import telebot
from telebot import types
import logging
from datetime import datetime
import threading
import time

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- BOT TOKEN ---
BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN)

# --- REQUIRED CHANNELS ---
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@bsb_chsb_8_sinf_uchun"},
    {"name": "3-kanal", "username": "@chsb_original"},
]

# --- LINKS ---
LINKS = {
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
}

# --- ADMIN ID ---
ADMIN_ID = 2051084228

# --- USERS FILE ---
USERS_FILE = "users.txt"
if not os.path.exists(USERS_FILE):
    open(USERS_FILE, "w").close()

# --- BROADCAST FLAGS ---
broadcast_running = False
broadcast_cancelled = False

# --- FUNCTIONS ---
def save_user(user_id, first_name):
    try:
        with open(USERS_FILE, "r") as f:
            users = [line.strip().split(",") for line in f.read().splitlines()]
    except FileNotFoundError:
        users = []

    if not any(u[0] == str(user_id) for u in users):
        today = datetime.now().strftime("%Y-%m-%d")
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id},{first_name},{today},0\n")

def increase_message_count(user_id):
    try:
        with open(USERS_FILE, "r") as f:
            users = [line.strip().split(",") for line in f.read().splitlines()]
    except FileNotFoundError:
        return

    updated = []
    for u in users:
        if u[0] == str(user_id):
            u[3] = str(int(u[3]) + 1)
        updated.append(u)
    with open(USERS_FILE, "w") as f:
        f.write("\n".join([",".join(u) for u in updated]))

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
    markup = types.InlineKeyboardMarkup()
    channels = REQUIRED_CHANNELS if not_subscribed is None else [c for c in REQUIRED_CHANNELS if c['name'] in not_subscribed]
    for channel in channels:
        markup.add(types.InlineKeyboardButton(channel['name'], url=f"https://t.me/{channel['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
    return markup

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
            bot.answer_callback_query(message_or_call.id, "Obuna bo‘lish kerak", show_alert=True)
            bot.edit_message_text(chat_id=chat_id, message_id=message_or_call.message.message_id, text=msg, reply_markup=markup)
        else:
            bot.send_message(chat_id, msg, reply_markup=markup)
        return False
    return True

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("BSB JAVOBLARI✅"), types.KeyboardButton("CHSB JAVOBLARI📎"))
    return markup

def admin_panel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📢 Xabar yuborish"), types.KeyboardButton("📊 Statistika"))
    markup.add(types.KeyboardButton("🔕 Broadcasting bekor qilish"), types.KeyboardButton("🏠 Bosh menyu"))
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    save_user(message.from_user.id, message.from_user.first_name)
    welcome = f"👋 Salom {message.from_user.first_name}!\nBotimizga xush kelibsiz 🎉\n\n" \
              f"📚 BSB va CHSB javoblari uchun, avval kanallarga obuna bo‘ling va “✅ Tekshirish” tugmasini bosing ⬇️"
    bot.send_message(message.chat.id, welcome, reply_markup=subscription_buttons())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz.")
        return
    bot.send_message(message.chat.id, "🔐 Admin panel:", reply_markup=admin_panel_markup())

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs(call):
    if check_user_subscriptions(call):
        chat_id = call.message.chat.id
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="✅ Siz barcha kanallarga obuna bo‘lgansiz!\nEndi botdan foydalanishingiz mumkin 🎉")
        bot.send_message(chat_id, "Asosiy menyu:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "BSB JAVOBLARI✅")
def bsb_handler(message):
    if not check_user_subscriptions(message): return
    increase_message_count(message.from_user.id)
    bot.send_message(message.chat.id, f"📚 8-sinf BSB javoblari:\n{LINKS['bsb_8']}")

@bot.message_handler(func=lambda m: m.text == "CHSB JAVOBLARI📎")
def chsb_handler(message):
    if not check_user_subscriptions(message): return
    increase_message_count(message.from_user.id)
    bot.send_message(message.chat.id, f"❗️ 8-sinf CHSB javoblari:\n{LINKS['chsb_8']}")

# --- BROADCAST (ADMIN) ---
def broadcast_message(text):
    global broadcast_running, broadcast_cancelled
    broadcast_running = True
    broadcast_cancelled = False
    try:
        with open(USERS_FILE, "r") as f:
            users = [line.strip().split(",")[0] for line in f.read().splitlines() if line]
    except FileNotFoundError:
        users = []

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
            continue
        if (i+1) % 30 == 0:
            time.sleep(1)
        if (i+1) % 100 == 0 or (i+1) == total:
            bot.send_message(ADMIN_ID, f"📊 Progress: {i+1}/{total} | Yuborildi: {sent}")
    broadcast_running = False
    bot.send_message(ADMIN_ID, f"✅ Broadcasting yakunlandi!\nJami yuborilgan: {sent}/{total}")

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")
def broadcast_start(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "📢 Xabar matnini yuboring:")
    bot.register_next_step_handler(msg, lambda m: threading.Thread(target=broadcast_message, args=(m.text,)).start())

@bot.message_handler(func=lambda m: m.text == "🔕 Broadcasting bekor qilish")
def cancel_broadcast(message):
    global broadcast_cancelled
    if message.from_user.id != ADMIN_ID: return
    broadcast_cancelled = True
    bot.send_message(message.chat.id, "❌ Broadcasting bekor qilindi!")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats_handler(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        with open(USERS_FILE, "r") as f:
            users = [line.strip().split(",") for line in f.read().splitlines() if line]
    except FileNotFoundError:
        users = []
    total = len(users)
    today = datetime.now().strftime("%Y-%m-%d")
    today_new = len([u for u in users if u[2] == today])
    top_users = sorted(users, key=lambda x: int(x[3]), reverse=True)[:10]
    top_list = "\n".join([f"{i+1}. {u[1]} — {u[3]} xabar" for i, u in enumerate(top_users)]) or "Hozircha ma'lumot yo‘q"
    bot.send_message(message.chat.id,
                     f"📊 <b>Statistika:</b>\n👥 Jami foydalanuvchilar: {total}\n🆕 Bugun qo‘shilganlar: {today_new}\n\n🔥 Eng faol foydalanuvchilar:\n{top_list}",
                     parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh menyu")
def return_main_menu(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔐 Admin panel:", reply_markup=admin_panel_markup())
    else:
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu())

# --- MESSAGE COUNTER ---
@bot.message_handler(content_types=['text'])
def message_counter(message):
    if not message.text.startswith("/"):
        increase_message_count(message.from_user.id)

# --- WEBHOOK ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})

def set_webhook():
    url = f"https://eight-sinf-bot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=url)

# --- MAIN ---
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

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

# --- TOKEN ---
BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# --- KANALLAR ---
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@bsb_chsb_8_sinf_uchun"},
    {"name": "3-kanal", "username": "@chsb_original"},
    {"name": "4-kanal", "username": "@kulishamiz_keling"},
]

# --- LINKLAR ---
LINKS = {
    "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
}

# --- ADMIN ID ---
ADMIN_ID = 2051084228

# --- FAYLLAR ---
USERS_FILE = "users.txt"
BROADCAST_FILE = "broadcast_status.txt"

if not os.path.exists(USERS_FILE):
    open(USERS_FILE, "w").close()

# --- FOYDALANUVCHI SAQLASH ---
def save_user(user_id, first_name):
    if not str(user_id) in open(USERS_FILE).read():
        today = datetime.now().strftime("%Y-%m-%d")
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id},{first_name},{today},0\n")

# --- XABAR SONI OSHIRISH ---
def increase_message_count(user_id):
    lines = []
    updated = False
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 4 and parts[0] == str(user_id):
                    parts[3] = str(int(parts[3]) + 1)
                    updated = True
                f.write(",".join(parts) + "\n")
    except: pass

# --- OBUNA TEKSHIRISH ---
def check_subscription_status(user_id):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
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

# --- MENYULAR ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("BSB JAVOBLARI✅", "CHSB JAVOBLARI📎")
    return markup

def admin_panel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📢 Xabar yuborish")
    btn2 = types.KeyboardButton("📊 Statistika")
    btn3 = types.KeyboardButton("🔕 Broadcasting bekor qilish")
    btn4 = types.KeyboardButton("🏠 Bosh menyu")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

# --- BROADCAST JARAYONI (fon rejimida) ---
broadcast_running = False
broadcast_cancelled = False

def broadcast_message(text, photo=None, document=None):
    global broadcast_running, broadcast_cancelled
    broadcast_running = True
    broadcast_cancelled = False

    users = []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                users.append(line.strip().split(",")[0])

    total = len(users)
    sent = 0
    failed = 0

    bot.send_message(ADMIN_ID, f"🚀 Broadcasting boshlandi...\nJami foydalanuvchilar: {total}")

    for i, user_id in enumerate(users):
        if broadcast_cancelled:
            bot.send_message(ADMIN_ID, "❌ Broadcasting to‘xtatildi.")
            break

        try:
            if photo:
                bot.send_photo(user_id, photo, caption=text, parse_mode="HTML")
            elif document:
                bot.send_document(user_id, document, caption=text, parse_mode="HTML")
            else:
                bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
            sent += 1
        except Exception as e:
            failed += 1

        # Har 30 ta xabardan keyin pauza (Telegram limitlaridan himoya)
        if (i + 1) % 30 == 0:
            time.sleep(1)

        # Adminga progress yuborish
        if (i + 1) % 100 == 0 or (i + 1) == total:
            bot.send_message(ADMIN_ID, f"📊 Progress: {i+1}/{total}\n✅ Yuborildi: {sent} | ❌ Xato: {failed}")

    broadcast_running = False
    result = f"✅ Broadcasting yakunlandi!\n\n📈 Natija:\nYuborildi: {sent}\nXato: {failed}\nJami: {total}"
    bot.send_message(ADMIN_ID, result)

# ==================== HANDLERLAR ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    save_user(message.from_user.id, message.from_user.first_name or "Foydalanuvchi")
    welcome = f"""👋 Assalomu alaykum, <b>{message.from_user.first_name}</b>!

📚 8-sinf BSB va CHSB javoblari uchun botga xush kelibsiz!

❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling va “✅ Tekshirish” tugmasini bosing 👇"""
    bot.send_message(message.chat.id, welcome, reply_markup=subscription_buttons(), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Sizda bunga ruxsat yo‘q.")
    bot.send_message(message.chat.id, "🔐 <b>Admin panelga xush kelibsiz!</b>", reply_markup=admin_panel_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs(call):
    not_subscribed = check_subscription_status(call.from_user.id)
    if not_subscribed:
        msg = "❌ Quyidagi kanallarga obuna bo‘lmagansiz:\n\n" + "\n".join(f"• {name}" for name in not_subscribed)
        bot.answer_callback_query(call.id, "Obuna bo‘lmagansiz!", show_alert=True)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=subscription_buttons(not_subscribed))
    else:
        bot.answer_callback_query(call.id, "Muvaffaqiyatli!")
        bot.edit_message_text("✅ Barcha kanallarga obuna bo‘ldingiz!\nEndi botdan foydalanishingiz mumkin 🎉",
                              call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🏠 Asosiy menyu:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "BSB JAVOBLARI✅")
def bsb_handler(message):
    if not check_user_subscriptions(message): return
    increase_message_count(message.from_user.id)
    bot.send_message(message.chat.id, f"📚 <b>8-sinf BSB javoblari:</b>\n\n{LINKS['bsb_8']}", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "CHSB JAVOBLARI📎")
def chsb_handler(message):
    if not check_user_subscriptions(message): return
    increase_message_count(message.from_user.id)
    bot.send_message(message.chat.id, f"❗️ <b>8-sinf CHSB javoblari:</b>\n\n{LINKS['chsb_8']}", parse_mode="HTML")

# --- YANGI MUKAMMAL BROADCAST ---
@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")
def broadcast_start(message):
    if message.from_user.id != ADMIN_ID: return
    if broadcast_running:
        return bot.reply_to(message, "⚠️ Hozirda broadcasting jarayoni davom etmoqda!")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast"))
    msg = bot.send_message(message.chat.id, 
        "📢 <b>Yuboriladigan xabarni yuboring:</b>\n\n"
        "• Matn\n"
        "• Foto + izoh\n"
        "• Dokument + izoh\n\n"
        "Yuborayotganingizni kuting...", 
        reply_markup=markup, parse_mode="HTML")
    
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    if message.from_user.id != ADMIN_ID: return

    text = message.caption if (message.photo or message.document) else message.text
    if not text:
        return bot.reply_to(message, "❌ Xabar matni bo‘sh!")

    # Thread orqali fon rejimida yuborish
    thread = threading.Thread(target=broadcast_message, args=(
        text,
        message.photo[-1].file_id if message.photo else None,
        message.document.file_id if message.document else None
    ))
    thread.start()

    bot.reply_to(message, "✅ Broadcasting boshlandi! Jarayon fon rejimida davom etmoqda...")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def cancel_broadcast(call):
    global broadcast_cancelled
    if call.from_user.id != ADMIN_ID: return
    broadcast_cancelled = True
    bot.answer_callback_query(call.id, "Broadcast bekor qilindi!")

@bot.message_handler(func=lambda m: m.text == "🔕 Broadcasting bekor qilish")
def force_stop_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    global broadcast_cancelled
    broadcast_cancelled = True
    bot.reply_to(message, "🔴 Broadcasting majburan to‘xtatildi!")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats_handler(message):
    if message.from_user.id != ADMIN_ID: return

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = [line.strip().split(",") for line in f.readlines() if line.strip()]
    except:
        users = []

    total = len(users)
    today = datetime.now().strftime("%Y-%m-%d")
    today_new = sum(1 for u in users if len(u) > 2 and u[2] == today)

    top_users = sorted(users, key=lambda x: int(x[3]) if len(x)>3 and x[3].isdigit() else 0, reverse=True)[:10]
    top_text = "\n".join([f"{i+1}. {u[1]} — <b>{u[3]}</b> ta xabar" for i, u in enumerate(top_users)]) if top_users else "Hali hech kim yo‘q"

    text = f"""
📊 <b>BOT STATISTIKASI</b>

👥 Jami foydalanuvchilar: <b>{total}</b>
🆕 Bugun qo‘shilganlar: <b>{today_new}</b>
📅 Bugungi sana: <code>{today}</code>

🔥 <b>Eng faol 10 ta foydalanuvchi:</b>
{top_text}
    """
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh menyu" or m.text == "🏠 Asosiy menyu")
def back_to_main(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔐 Admin panel", reply_markup=admin_panel_markup())
    else:
        bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu())

# Barcha matnli xabarlarni hisoblash
@bot.message_handler(content_types=['text', 'photo', 'document'])
def count_all_messages(message):
    if message.from_user.id != ADMIN_ID and not message.text.startswith("/"):
        increase_message_count(message.from_user.id)

# ==================== WEBHOOK ====================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot ishlamoqda!"

# ==================== MAIN ====================
def set_webhook():
    url = f"https://eight-sinf-bot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    time.sleep(1)
    if bot.set_webhook(url):
        logger.info("Webhook muvaffaqiyatli o‘rnatildi!")
    else:
        logger.error("Webhook o‘rnatilmadi!")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)







import telebot

BOT_TOKEN = "8169442989:AAGDoHlUu6o54zadUYOemWX1k0VOsqZbd_c"
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()
print("Webhook o'chirildi!")

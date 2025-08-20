from telegram import Bot

BOT_TOKEN = "8417540455:AAHowzwxGRwT1BTA5sC6vO1xkBhvMeBry7U"
bot = Bot(token=BOT_TOKEN)

# Hapus webhook
bot.delete_webhook()
print("✅ Webhook dihapus. Bot siap untuk polling.")

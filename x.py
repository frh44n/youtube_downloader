import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

load_dotenv()

# Telegram bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Set webhook URL path
WEBHOOK_URL_PATH = "/webhook"

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Bot command functions
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! Send me a YouTube video link to download.")

def download_video(update, context):
    if not context.args:
        update.message.reply_text("Please provide a YouTube video link.")
        return

    video_link = context.args[0]
    # Implement your YouTube video downloading logic here
    # Example: Download the video and send it back to the user
    # Replace with your actual downloading logic
    update.message.reply_text(f"Downloading video from {video_link}...")

def webhook(request):
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

def main():
    # Set webhook
    bot.set_webhook(f"https://{os.getenv('APP_NAME')}.herokuapp.com{WEBHOOK_URL_PATH}")

    # Add handlers for commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("download", download_video, pass_args=True))

    # Start the Flask web server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()

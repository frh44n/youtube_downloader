import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

load_dotenv()

# Telegram bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Set webhook URL path
WEBHOOK_URL_PATH = f"/{BOT_TOKEN}"

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

    # Example: Ask the user to select a format
    keyboard = [
        [
            InlineKeyboardButton("480p", callback_data=f"format_480|{video_link}"),
            InlineKeyboardButton("720p", callback_data=f"format_720|{video_link}")
        ],
        [
            InlineKeyboardButton("1080p", callback_data=f"format_1080|{video_link}"),
            InlineKeyboardButton("MP3", callback_data=f"format_mp3|{video_link}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose the format:", reply_markup=reply_markup)

def button(update, context):
    query = update.callback_query
    query.answer()
    
    # Extract the format and video link from the callback data
    format, video_link = query.data.split('|')
    
    # Implement your YouTube video downloading logic here based on the format
    # Example:
    video_path = download_video_from_youtube(video_link, format)
    
    # Send the downloaded video to the user
    with open(video_path, 'rb') as video_file:
        if format == 'format_mp3':
            context.bot.send_audio(chat_id=query.message.chat_id, audio=video_file)
        else:
            context.bot.send_video(chat_id=query.message.chat_id, video=video_file)

    query.edit_message_text(text=f"Downloaded video in {format} format from {video_link}")

# Function to download video from YouTube (placeholder, implement actual logic)
def download_video_from_youtube(video_link, format):
    # Replace with actual logic to download the video
    # and return the path to the downloaded video
    # Placeholder for demonstration
    if format == "format_480":
        return "/path/to/downloaded/video_480.mp4"
    elif format == "format_720":
        return "/path/to/downloaded/video_720.mp4"
    elif format == "format_1080":
        return "/path/to/downloaded/video_1080.mp4"
    else:  # format_mp3
        return "/path/to/downloaded/audio.mp3"

@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

def main():
    # Set webhook
    bot.set_webhook(f"https://x-py.onrender.com{WEBHOOK_URL_PATH}")

    # Add handlers for commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("download", download_video, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Start the Flask web server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()

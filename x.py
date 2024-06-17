from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from pytube import YouTube
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', '5000'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Ensure this is correctly set in your Render environment

def start(update: Update, context: CallbackContext) -> None:
    user_first_name = update.effective_user.first_name
    update.message.reply_text(f"Welcome {user_first_name}, Send me YouTube Video url, I will give video in your preferred format.")

def handle_link(update: Update, context: CallbackContext) -> None:
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        update.message.reply_text("Please send me YouTube link only.")
        return

    context.user_data['url'] = url

    keyboard = [
        [
            InlineKeyboardButton("480p", callback_data='480p'),
            InlineKeyboardButton("720p", callback_data='720p'),
        ],
        [
            InlineKeyboardButton("1080p", callback_data='1080p'),
            InlineKeyboardButton("MP3", callback_data='mp3'),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Select video format:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    format = query.data
    url = context.user_data['url']
    query.edit_message_text(text=f"Please wait: Downloading {format} format")

    try:
        yt = YouTube(url)
        if format == 'mp3':
            stream = yt.streams.filter(only_audio=True).first()
            file_path = stream.download()
            base, ext = os.path.splitext(file_path)
            new_file = base + '.mp3'
            os.rename(file_path, new_file)
        else:
            stream = yt.streams.filter(res=format).first()
            stream.download()

        query.edit_message_text(text="Download completed. Sending the file...")

        if format == 'mp3':
            context.bot.send_audio(chat_id=query.message.chat_id, audio=open(new_file, 'rb'))
            os.remove(new_file)
        else:
            video_file = stream.default_filename
            context.bot.send_video(chat_id=query.message.chat_id, video=open(video_file, 'rb'))
            os.remove(video_file)

    except Exception as e:
        query.edit_message_text(text=f"An error occurred: {str(e)}")

def main() -> None:
    updater = Updater(BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Set up webhook
    updater.start_webhook(listen="0.0.0.0",  # Listen on all available interfaces
                          port=PORT,
                          url_path=BOT_TOKEN)
    
    # Set the webhook URL provided by Render
    updater.bot.set_webhook(WEBHOOK_URL + BOT_TOKEN)

    updater.idle()

if __name__ == '__main__':
    main()

import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from pytube import YouTube

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Telegram bot token (replace with your bot token)
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Define the available video formats
VIDEO_FORMATS = {
    '480p': 'medium',
    '720p': '720p',
    '1080p': '1080p',
    '2K': '1440p',
}

# Handler function for /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(
        f"Hello {user.first_name}! I'm a YouTube video downloader bot. Just send me the YouTube video URL and I'll provide you with download options."
    )

# Handler function for processing YouTube video download requests
def download_video(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    video_url = query.data

    keyboard = []

    for format_name, resolution in VIDEO_FORMATS.items():
        video = YouTube(video_url)
        stream = video.streams.filter(res=resolution).first()

        if stream:
            keyboard.append([InlineKeyboardButton(format_name, callback_data=f'download_{resolution}')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Choose a format to download:",
        reply_markup=reply_markup
    )

# Handler function for processing download format selection
def process_download(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    resolution = query.data.split('_')[1]

    video = YouTube(query.message.reply_to_message.text)
    stream = video.streams.filter(res=resolution).first()

    if stream:
        stream.download(filename=f'{video.title}.mp4')
        context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open(f'{video.title}.mp4', 'rb'),
            caption=f'Download complete for {resolution}',
        )
        os.remove(f'{video.title}.mp4')
    else:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f'Format {resolution} not available for this video.'
        )

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(download_video, pattern=r'^https://www.youtube.com/'))
    dispatcher.add_handler(CallbackQueryHandler(process_download, pattern=r'^download_'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

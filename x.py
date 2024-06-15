import os
import logging
from telegram.ext import (Filters, Updater, CommandHandler, CallbackQueryHandler, MessageHandler)
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Fetch environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Your Telegram bot token
ADMIN_ID = os.environ.get("ADMIN_ID")  # Your Telegram user ID
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")  # Render external hostname
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")  # Path to Firebase service account key
PORT = int(os.environ.get("PORT", 5000))  # Port for webhook

# Initialize Firebase Admin SDK
cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm a bot. You can subscribe to me by clicking the button below.")
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Subscribe",
        reply_markup={
            "inline_keyboard": [[{"text": "Subscribe", "callback_data": "subscribe"}]]
        }
    )

def subscribe(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    doc_ref = db.collection('subscribers').document(str(user_id))
    doc = doc_ref.get()

    if doc.exists:
        query.answer("User is already subscribed.")
    else:
        doc_ref.set({"subscribed": True})
        query.answer("Successfully Subscribed!")

def broadcast(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        message = update.message.text.split(" ", 1)[1]
        subscribers_ref = db.collection('subscribers')
        subscribers = subscribers_ref.stream()

        for subscriber in subscribers:
            subscriber_id = int(subscriber.id)
            try:
                context.bot.send_message(chat_id=subscriber_id, text=message)
            except Exception as e:
                logging.error(f"Error sending message to {subscriber_id}: {e}")
    else:
        update.message.reply_text("Only the admin can send broadcasts.")

def subscribers(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        subscribers_ref = db.collection('subscribers')
        total_subscribers = len(list(subscribers_ref.stream()))
        update.message.reply_text(f"Total subscribers: {total_subscribers}")
    else:
        update.message.reply_text("Only the admin can check subscribers.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add handlers for commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("subscribers", subscribers))

    # Add handler for inline button clicks
    dispatcher.add_handler(CallbackQueryHandler(subscribe))

    # Set up webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}",
    )

    # Start the bot
    updater.idle()

if __name__ == "__main__":
    main()

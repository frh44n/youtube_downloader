import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Initialize Firebase app using the service account key from the environment variable
cred = credentials.Certificate(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
firebase_admin.initialize_app(cred)

db = firestore.client()

# Bot command functions
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm a bot. You can subscribe to me by clicking the button below.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Subscribe", reply_markup={"inline_keyboard": [[{"text": "Subscribe", "callback_data": "subscribe"}]]})

def subscribe(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    doc_ref = db.collection('subscribers').document(str(user_id))
    if doc_ref.get().exists:
        query.answer("User is already subscribed.")
    else:
        doc_ref.set({'subscribed': True})
        query.answer("Successfully Subscribed!")

def broadcast(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        message = update.message.text.split(" ", 1)[1]
        docs = db.collection('subscribers').stream()
        for doc in docs:
            subscriber_id = doc.id
            try:
                context.bot.send_message(chat_id=subscriber_id, text=message)
            except Exception as e:
                logging.error(f"Error sending message to {subscriber_id}: {e}")
    else:
        update.message.reply_text("Only the admin can send broadcasts.")

def subscribers(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        total_subscribers = len(list(db.collection('subscribers').stream()))
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

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

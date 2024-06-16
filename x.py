import os
import logging
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME")
PORT = int(os.environ.get("PORT", 5000))

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
subscribers_collection = db['subscribers']

# Initialize Flask app
app = Flask(__name__)

# Bot command functions
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Best bot for Videos 🔥 🔥.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Press Subscribe to start receiving videos daily", reply_markup={"inline_keyboard": [[{"text": "Subscribe", "callback_data": "subscribe"}]]})

def subscribe(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    if subscribers_collection.find_one({"user_id": user_id}):
        query.answer("User is already subscribed.")
    else:
        subscribers_collection.insert_one({"user_id": user_id})
        query.answer("Successfully Subscribed!")

def broadcast(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        message = update.message.text.split(" ", 1)[1]
        subscribers = subscribers_collection.find()
        for subscriber in subscribers:
            subscriber_id = subscriber['user_id']
            try:
                context.bot.send_message(chat_id=subscriber_id, text=message)
            except Exception as e:
                logging.error(f"Error sending message to {subscriber_id}: {e}")
    else:
        update.message.reply_text("Only the admin can send broadcasts.")

def subscribers(update, context):
    if update.effective_user.id == int(ADMIN_ID):
        total_subscribers = subscribers_collection.count_documents({})
        update.message.reply_text(f"Total subscribers: {total_subscribers}")
    else:
        update.message.reply_text("Only the admin can check subscribers.")

# Webhook endpoint
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.json, context.bot)
    dispatcher.process_update(update)
    return jsonify({'status': 'ok'})

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher

    # Add handlers for commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("subscribers", subscribers))

    # Add handler for inline button clicks
    dispatcher.add_handler(CallbackQueryHandler(subscribe))

    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=BOT_TOKEN,
                          webhook_url=f"https://x-py.onrender.com/{BOT_TOKEN}")

    # Run Flask app
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()

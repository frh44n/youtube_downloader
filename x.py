import os
import logging
import mysql.connector
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
WEBHOOK_URL_PATH = os.environ.get("WEBHOOK_URL_PATH", "/")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") + WEBHOOK_URL_PATH

# Initialize MySQL connection
mysql_conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)
mysql_cursor = mysql_conn.cursor()

# Bot command functions
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Best bot for Videos 🔥 🔥.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Press Subscribe to start receiving videos daily", reply_markup={"inline_keyboard": [[{"text": "Subscribe", "callback_data": "subscribe"}]]})

def subscribe(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    # Check if user is already subscribed
    mysql_cursor.execute("SELECT * FROM subscribers WHERE user_id = %s", (user_id,))
    if mysql_cursor.fetchone():
        query.answer("User is already subscribed.")
    else:
        # Insert user into database
        mysql_cursor.execute("INSERT INTO subscribers (user_id) VALUES (%s)", (user_id,))
        mysql_conn.commit()
        query.answer("Successfully Subscribed!")

def broadcast(update, context):
    if update.effective_user.id == ADMIN_ID:
        message = update.message.text.split(" ", 1)[1]
        mysql_cursor.execute("SELECT user_id FROM subscribers")
        subscribers = mysql_cursor.fetchall()
        for subscriber in subscribers:
            subscriber_id = subscriber[0]
            try:
                context.bot.send_message(chat_id=subscriber_id, text=message)
            except Exception as e:
                logging.error(f"Error sending message to {subscriber_id}: {e}")
    else:
        update.message.reply_text("Only the admin can send broadcasts.")

def subscribers(update, context):
    if update.effective_user.id == ADMIN_ID:
        mysql_cursor.execute("SELECT COUNT(*) FROM subscribers")
        total_subscribers = mysql_cursor.fetchone()[0]
        update.message.reply_text(f"Total subscribers: {total_subscribers}")
    else:
        update.message.reply_text("Only the admin can check subscribers.")

# Webhook handler
@app.route(WEBHOOK_URL_PATH + BOT_TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.json, context.bot)
    dispatcher.process_update(update)
    return 'ok'

def main():
    global dispatcher

    # Create Telegram bot updater
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers for commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("subscribers", subscribers))

    # Register handler for inline button clicks
    dispatcher.add_handler(CallbackQueryHandler(subscribe))

    # Start the webhook
    updater.start_webhook(listen="https://x-py.onrender.com",
                          port=int(os.environ.get('PORT', 5000)),
                          url_path=BOT_TOKEN)
    updater.bot.set_webhook(WEBHOOK_URL + BOT_TOKEN)

    # Start the Flask web server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    main()

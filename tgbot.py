import os
import logging
import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from elasticpath import get_all_products, get_elasticpath_token


_database = None
logger = logging.getLogger(__name__)
load_dotenv()


def start(bot, update):
    store_token = get_elasticpath_token('elasticpath_token')
    store_id = os.getenv('STORE_ID')
    products = get_all_products(store_token, store_id)['data']
    keyboard = []
    for product in products:
        product_name = product['attributes']['name']
        product_id = product['id']
        keyboard.append([InlineKeyboardButton(product_name, callback_data=product_id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Welcome to the Store!', reply_markup=reply_markup)
    return "HANDLE_MENU"


def button(bot, update):
    query = update.callback_query
    bot.edit_message_text(text=f"Selected product: {query.data}",
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    return "BUTTON"


def handle_users_reply(bot, update):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    states_functions = {'START': start,
                        'BUTTON': button}
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(str(chat_id), str(next_state))
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv("REDIS_PASSWORD")
        database_url = os.getenv("REDIS_URL")
        database_port = os.getenv("REDIS_PORT")
        _database = redis.Redis(host=database_url, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    load_dotenv()
    token = os.getenv("TG_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()

import os
import logging
import redis
from enum import Enum, auto
from functools import partial
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, ConversationHandler
from elasticpath import get_all_products, \
    get_photo_by_productid, \
    get_elasticpath_token, \
    get_client_token, \
    set_elasticpath_token, \
    is_token_expired

_database = None
logger = logging.getLogger(__name__)


class State(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()


def get_product_keyboard(products):
    keyboard = []
    for product in products['data']:
        product_name = product['attributes']['name']
        product_id = product['id']
        keyboard.append([InlineKeyboardButton(product_name, callback_data=product_id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update, token_filename, store_id, client_id, client_secret):
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    products = get_all_products(elasticpath_token, store_id)
    keyboard = get_product_keyboard(products)
    update.message.reply_text(text='Welcome to the Store!', reply_markup=keyboard)
    return State.HANDLE_DESCRIPTION


def handle_description(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    product_id = query.data
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    photo_link = get_photo_by_productid(elasticpath_token, product_id, store_id)
    keyboard = [[InlineKeyboardButton('Back', callback_data='Back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    bot.send_photo(chat_id=query.message.chat_id,
                   photo=photo_link,
                   reply_markup=reply_markup)
    '''
    bot.sendPhoto(chat_id=query.message.chat_id,
                  photo=photo_link,
                  message_id=query.message.message_id,
                  text=f"Selected product: {query.data}",
                  reply_markup=reply_markup)
    '''

    '''
    bot.edit_message_text(text=f"Selected product: {query.data}",
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          reply_markup=reply_markup)
    '''
    return State.HANDLE_MENU


def handle_menu(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    print(query)
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    products = get_all_products(elasticpath_token, store_id)
    keyboard = get_product_keyboard(products)
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    bot.send_message(text=f"Let's continue",
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     reply_markup=keyboard)
    return State.HANDLE_DESCRIPTION


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv("REDIS_PASSWORD")
        database_url = os.getenv("REDIS_URL")
        database_port = os.getenv("REDIS_PORT")
        _database = redis.Redis(host=database_url, port=database_port, password=database_password)
    return _database


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    store_id = os.getenv('STORE_ID')
    store_token = get_elasticpath_token('elasticpath_token')
    token_filename = 'elasticpath_token'
    products = get_all_products(store_token, store_id)

    updater = Updater(tg_token)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', partial(start,
                                                      token_filename=token_filename,
                                                      store_id=store_id,
                                                      client_id=client_id,
                                                      client_secret=client_secret))],
        states={State.HANDLE_DESCRIPTION: [CallbackQueryHandler(partial(handle_description,
                                                                        token_filename=token_filename,
                                                                        store_id=store_id,
                                                                        client_id=client_id,
                                                                        client_secret=client_secret))],
                State.HANDLE_MENU: [CallbackQueryHandler(partial(handle_menu,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret
                                                                 ))]},
        fallbacks=[])

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

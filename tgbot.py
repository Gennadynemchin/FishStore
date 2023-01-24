import os
import logging
import redis
from enum import Enum, auto
from functools import partial
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, ConversationHandler
from elasticpath import get_all_products, \
    get_product_by_id, \
    get_photo_by_productid, \
    get_elasticpath_token, \
    get_client_token, \
    set_elasticpath_token, \
    is_token_expired, \
    add_product_to_cart, \
    get_cart_items


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
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    product_info = get_product_by_id(elasticpath_token, product_id, store_id)
    photo_link = get_photo_by_productid(elasticpath_token, product_id, store_id)
    keyboard = [[InlineKeyboardButton('Add to cart', callback_data=f'add_to_cart {product_id}')],
                [InlineKeyboardButton('Go to cart', callback_data='cart_info')],
                [InlineKeyboardButton('Back', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    bot.send_photo(chat_id=query.message.chat_id,
                   caption=product_info,
                   photo=photo_link,
                   reply_markup=reply_markup)
    return State.HANDLE_DESCRIPTION


def add_to_cart(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    cart_id = update.effective_user.id
    product_id = query.data.split(' ')[1]
    quantity = 1
    add_product_to_cart(elasticpath_token, cart_id, store_id, product_id, quantity)
    print('ADDED 2 CART')
    return State.HANDLE_DESCRIPTION


def handle_cart_info(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    cart_info = get_cart_items(elasticpath_token, cart_id, store_id)
    pass



def handle_menu(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    products = get_all_products(elasticpath_token, store_id)
    keyboard = get_product_keyboard(products)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
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
        states={State.HANDLE_DESCRIPTION: [CallbackQueryHandler(partial(add_to_cart,
                                                                        token_filename=token_filename,
                                                                        store_id=store_id,
                                                                        client_id=client_id,
                                                                        client_secret=client_secret),
                                                                pattern='^add_to_cart'),
                                           CallbackQueryHandler(partial(handle_menu,
                                                                        token_filename=token_filename,
                                                                        store_id=store_id,
                                                                        client_id=client_id,
                                                                        client_secret=client_secret),
                                                                pattern='back'),
                                           CallbackQueryHandler(partial(handle_description,
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

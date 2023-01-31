import os
import logging
import redis
from enum import Enum, auto
from functools import partial
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater
from telegram.ext import CallbackQueryHandler, \
    CommandHandler, \
    ConversationHandler
from elasticpath import get_all_products, \
    get_product_by_id, \
    get_photo_by_productid, \
    get_elasticpath_token, \
    get_client_token, \
    set_elasticpath_token, \
    is_token_expired, \
    add_product_to_cart, \
    get_cart_items, \
    remove_all_from_cart

_database = None
logger = logging.getLogger(__name__)


class State(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()


def handle_menu(bot, update, token_filename, store_id, client_id, client_secret):
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    products = get_all_products(elasticpath_token, store_id)
    keyboard = []
    for product in products['data']:
        product_name = product['attributes']['name']
        product_id = product['id']
        keyboard.append([InlineKeyboardButton(product_name, callback_data=product_id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    update.effective_message.reply_text(text=f"Let's choose:",
                                        reply_markup=reply_markup)
    return State.HANDLE_DESCRIPTION


def handle_description(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    product_id = query.data
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    product_info = get_product_by_id(elasticpath_token, product_id, store_id)
    product_name = product_info['data']['attributes']['name']
    product_price = product_info['data']['meta']['display_price']['with_tax']['formatted']
    product_sku = product_info['data']['attributes']['sku']
    photo_link = get_photo_by_productid(elasticpath_token, product_id, store_id)
    keyboard = [[InlineKeyboardButton('Add to cart', callback_data=f'add_to_cart {product_id}')],
                [InlineKeyboardButton('Go to cart', callback_data='cart_info')],
                [InlineKeyboardButton('Back', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    bot.send_photo(chat_id=query.message.chat_id,
                   caption=f'{product_name}\n{product_price}\n{product_sku}',
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
    query.answer(text='The product has been added to cart', show_alert=True)
    return State.HANDLE_DESCRIPTION


def handle_cart_info(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    cart_info = get_cart_items(elasticpath_token, cart_id, store_id)
    total_price = cart_info['meta']['display_price']['with_tax']['formatted']
    products_in_cart_info = []
    for product in cart_info['data']:
        name = product['name']
        sku = product['sku']
        qty = product['quantity']
        price = product['meta']['display_price']['with_tax']['unit']['formatted']
        product_total = product['meta']['display_price']['with_tax']['value']['formatted']
        message = (f'Name: {name}\n'
                   f'Qty: {qty}\n'
                   f'Price: {price}\n'
                   f'Subtotal: {product_total}\n\n')
        products_in_cart_info.append(message)
    keyboard = [[InlineKeyboardButton('Menu', callback_data='menu')],
                [InlineKeyboardButton('Remove all', callback_data='remove_all')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    bot.send_message(text=f'{" ".join(products_in_cart_info)}\n Total: {total_price}',
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     reply_markup=reply_markup)
    return State.HANDLE_CART


def handle_remove_all_from_cart(bot, update, token_filename, store_id, client_id, client_secret):
    query = update.callback_query
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)['access_token']
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    remove_all_from_cart(elasticpath_token, cart_id, store_id)
    keyboard = [[InlineKeyboardButton('Menu', callback_data='menu')]]
    query.answer(text='The product has been added to cart', show_alert=False)
    update.effective_message.delete()
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text='Now your cart is empty. Please go to "Menu"',
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     reply_markup=reply_markup)
    return State.HANDLE_CART


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
        entry_points=[CommandHandler('start', partial(handle_menu,
                                                      token_filename=token_filename,
                                                      store_id=store_id,
                                                      client_id=client_id,
                                                      client_secret=client_secret))],
        states={State.HANDLE_MENU: [CallbackQueryHandler(partial(handle_menu,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret
                                                                 ),
                                                         pattern='remove_all'),
                                    CallbackQueryHandler(partial(handle_menu,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret
                                                                 ))],
                State.HANDLE_DESCRIPTION: [CallbackQueryHandler(partial(add_to_cart,
                                                                        token_filename=token_filename,
                                                                        store_id=store_id,
                                                                        client_id=client_id,
                                                                        client_secret=client_secret),
                                                                pattern='^add_to_cart'),
                                           CallbackQueryHandler(partial(handle_cart_info,
                                                                        token_filename=token_filename,
                                                                        store_id=store_id,
                                                                        client_id=client_id,
                                                                        client_secret=client_secret),
                                                                pattern='cart_info'),
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
                State.HANDLE_CART: [CallbackQueryHandler(partial(handle_menu,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret),
                                                         pattern='menu'),
                                    CallbackQueryHandler(partial(handle_remove_all_from_cart,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret),
                                                         pattern='remove_all'),
                                    CallbackQueryHandler(partial(handle_cart_info,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret))
                                    ]},
        fallbacks=[])

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

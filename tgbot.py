import os
import logging
from enum import Enum, auto
from functools import partial
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater
from telegram.ext import CallbackQueryHandler, \
    CommandHandler, \
    ConversationHandler
from keyboards import get_all_products_keyboard
from elasticpath import get_all_products, \
    get_product_info_by_id, \
    get_photo_by_productid, \
    get_elasticpath_token, \
    get_client_token, \
    set_elasticpath_token, \
    is_token_expired, \
    add_product_to_cart, \
    get_cart_items, \
    remove_all_from_cart, \
    delete_product_from_cart

logger = logging.getLogger(__name__)


class State(Enum):
    START = auto()
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()


def handle_menu(bot, update, token_filename, store_id, client_id, client_secret):
    if is_token_expired(token_filename, store_id):
        token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(token, token_filename)
    elastic_token = get_elasticpath_token(token_filename)
    products = get_all_products(elastic_token, store_id)
    keyboard = []
    for product in products:
        product_name = product['attributes']['name']
        product_id = product['id']
        keyboard.append([InlineKeyboardButton(product_name, callback_data=product_id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    update.effective_message.reply_text(text=f"Let's choose:", reply_markup=reply_markup)
    return State.HANDLE_DESCRIPTION


def handle_description(bot, update, token_filename, store_id, client_id, client_secret):
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    product_id = update.callback_query.data
    product_info = get_product_info_by_id(elasticpath_token, product_id, store_id)
    product_name = product_info['product_name']
    product_description = product_info['product_description']
    product_price = product_info['product_price']
    product_sku = product_info['product_sku']
    photo_link = get_photo_by_productid(elasticpath_token, product_id, store_id)
    keyboard = [[InlineKeyboardButton('Buy 1kg', callback_data=f'add_to_cart {product_id} 1'),
                 InlineKeyboardButton('Buy 3kg', callback_data=f'add_to_cart {product_id} 3'),
                 InlineKeyboardButton('Buy 10kg', callback_data=f'add_to_cart {product_id} 10')],
                [InlineKeyboardButton('Go to cart', callback_data='cart_info')],
                [InlineKeyboardButton('Back', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    bot.send_photo(chat_id=update.callback_query.message.chat_id,
                   caption=f'{product_name}\n'
                           f'{product_description}\n'
                           f'{product_price}\n'
                           f'{product_sku}',
                   photo=photo_link,
                   reply_markup=reply_markup)
    return State.HANDLE_DESCRIPTION


def add_to_cart(bot, update, token_filename, store_id, client_id, client_secret):
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    cart_id = update.effective_user.id
    product_id = update.callback_query.data.split(' ')[1]
    quantity = int(update.callback_query.data.split(' ')[2])
    add_product_to_cart(elasticpath_token, cart_id, store_id, product_id, quantity)
    update.callback_query.answer(text='The product has been added to cart', show_alert=False)
    return State.HANDLE_DESCRIPTION


def handle_cart_info(bot, update, token_filename, store_id, client_id, client_secret):
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)

    cart_info, total_price = get_cart_items(elasticpath_token, cart_id, store_id)
    products_in_cart_info = []
    keyboard = [[InlineKeyboardButton('Menu', callback_data='menu'),
                 InlineKeyboardButton('Remove all', callback_data='remove_all')]]
    single_remove_keyboard = []
    for product in cart_info:
        id = product['id']
        name = product['name']
        qty = product['qty']
        price = product['price']
        product_subtotal = product['subtotal']
        message = f'Name: {name}\n Qty: {qty}\n Price: {price}\n Subtotal: {product_subtotal}\n\n'
        products_in_cart_info.append(message)
        single_remove_keyboard.append(InlineKeyboardButton(f'Delete {name}', callback_data=f'remove_item {id}'))
    keyboard.insert(0, single_remove_keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.delete()
    update.effective_user.send_message(text=f'{" ".join(products_in_cart_info)}\n Total: {total_price}',
                                       reply_markup=reply_markup)
    return State.HANDLE_CART

# переместить удаление в корзина инфо. Сделать один паттерн. В корзина инфо условие: если колбэк.дата == продукт айди
# то активируется кусок кода, удаляющий товар из корзины
# ^remove_item тоже активирует handle_cart_info

def remove_item_from_cart(bot, update, token_filename, store_id, client_id, client_secret):
    product_id = update.callback_query.data.split(' ')[1]
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    delete_product_from_cart(elasticpath_token, cart_id, store_id, product_id)
    update.effective_message.delete()

    cart_info, total_price = get_cart_items(elasticpath_token, cart_id, store_id)
    products_in_cart_info = []
    keyboard = [[InlineKeyboardButton('Menu', callback_data='menu'),
                 InlineKeyboardButton('Remove all', callback_data='remove_all')]]
    single_remove_keyboard = []
    for product in cart_info:
        id = product['id']
        name = product['name']
        qty = product['qty']
        price = product['price']
        product_subtotal = product['subtotal']
        message = f'Name: {name}\n Qty: {qty}\n Price: {price}\n Subtotal: {product_subtotal}\n\n'
        products_in_cart_info.append(message)
        single_remove_keyboard.append(InlineKeyboardButton(f'Delete {name}', callback_data=f'remove_item {id}'))
    keyboard.insert(0, single_remove_keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_user.send_message(text=f'{" ".join(products_in_cart_info)}\n Total: {total_price}',
                                       reply_markup=reply_markup)
    return State.HANDLE_CART


def handle_remove_all_from_cart(bot, update, token_filename, store_id, client_id, client_secret):
    cart_id = update.effective_user.id
    if is_token_expired(token_filename, store_id):
        new_token = get_client_token(client_id, client_secret, store_id)
        set_elasticpath_token(new_token, token_filename)
    elasticpath_token = get_elasticpath_token(token_filename)
    remove_all_from_cart(elasticpath_token, cart_id, store_id)
    keyboard = [[InlineKeyboardButton('Menu', callback_data='menu')]]
    update.callback_query.answer(text='The product has been added to cart', show_alert=False)
    update.effective_message.delete()
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text='Now your cart is empty. Please go to the "Menu"',
                     chat_id=update.callback_query.message.chat_id,
                     message_id=update.callback_query.message.message_id,
                     reply_markup=reply_markup)
    return State.HANDLE_CART


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    store_id = os.getenv('STORE_ID')
    token_filename = 'elasticpath_token'

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
                                    CallbackQueryHandler(partial(remove_item_from_cart,
                                                                 token_filename=token_filename,
                                                                 store_id=store_id,
                                                                 client_id=client_id,
                                                                 client_secret=client_secret),
                                                         pattern='^remove_item'),

                                    ]},
        fallbacks=[CommandHandler('start', partial(handle_menu,
                                                   token_filename=token_filename,
                                                   store_id=store_id,
                                                   client_id=client_id,
                                                   client_secret=client_secret))])

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

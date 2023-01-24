import os
import json
import requests
from dotenv import load_dotenv


def get_client_token(client_id, client_secret, store_id):
    url = 'https://useast.api.elasticpath.com/oauth/access_token'
    payload = f'client_id={client_id}&' \
              f'client_secret={client_secret}&' \
              'grant_type=client_credentials'
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded',
               'x-moltin-auth-store': store_id}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_all_products(token, store_id):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def create_cart(token, store_id, customer_id, cart_name, cart_description):
    url = 'https://useast.api.elasticpath.com/v2/carts'
    payload = json.dumps({"data": {"name": cart_name,
                                   "description": cart_description}})
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               # 'x-moltin-customer-token': customer_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_cart(token, cart_id, store_id):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}'
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def get_cart_items(token, cart_id, store_id):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def add_product_to_cart(token, cart_id, store_id, product_id, quantity: int):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items'
    payload = json.dumps({"data": {'id': product_id,
                                   # 'sku': '111111',
                                   'type': "cart_item",
                                   'quantity': quantity}})
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_product_by_id(token, product_id, store_id):
    url_get_fileid = f'https://useast.api.elasticpath.com/catalog/products/{product_id}'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url_get_fileid, headers=headers, data=payload)
    return response.json()


def get_price_by_pricebookid(token, pricebook_id, store_id):
    url = f'https://useast.api.elasticpath.com/pcm/pricebooks'
    # url = f'https://useast.api.elasticpath.com/pcm/pricebooks/{pricebook_id}/prices'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)


def get_photo_by_productid(token, product_id, store_id):
    url_get_fileid = f'https://useast.api.elasticpath.com/pcm/products/{product_id}/relationships/files'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url_get_fileid, headers=headers, data=payload)
    file_id = response.json()['data'][0]['id']

    url_get_photo = f'https://useast.api.elasticpath.com/v2/files/{file_id}'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url_get_photo, headers=headers, data=payload)
    file_link = response.json()['data']['link']['href']
    return file_link


def is_token_expired(filename, store_id):
    with open(filename, "r") as elasticpath_token:
        token = elasticpath_token.read()
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers)
    if response.json().get('errors') is not None:
        return True
    else:
        return False


def set_elasticpath_token(token, filename):
    with open(filename, "w") as elasticpath_token:
        elasticpath_token.write(token)
    return token


def get_elasticpath_token(filename):
    with open(filename, "r") as elasticpath_token:
        token = elasticpath_token.read()
    return token


def main():
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    store_id = os.getenv('STORE_ID')
    new_elasticpath_token = get_client_token(client_id, client_secret, store_id)['access_token']
    set_elasticpath_token(new_elasticpath_token, 'elasticpath_token')
    elasticpath_token = get_elasticpath_token('elasticpath_token')

    print(is_token_expired('elasticpath_token', store_id))
    products = get_all_products(elasticpath_token, store_id)
    print(products)
    # file = get_photo(elasticpath_token, '575e3013-fee0-43bc-8a32-2222de0e89de', store_id)
    # print(file)
    file = get_photo_by_productid(elasticpath_token, 'fd47ec2f-07ea-4933-9401-2028b98d3e16', store_id)
    print(file)
    pricebook = get_price_by_pricebookid(elasticpath_token, 'ed81b3de-44b6-4847-b9d0-f4e6ace58752', store_id)
    print(pricebook)
    # print(create_cart(token, store_id, 'test_123', 'test_cart', 'test_description'))
    # print(get_cart(token, 'test_123', store_id))
    # print(add_product_to_cart(token, 'test_123', store_id, '10280a0e-c310-4a03-ad3c-600e9e3978ea', 1))
    # cart_items = get_cart_items(elasticpath_token, 'test_123', store_id)


if __name__ == '__main__':
    main()

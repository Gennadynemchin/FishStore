import json
import requests
import os


def get_client_token(client_id, client_secret, store_id):
    url = 'https://useast.api.elasticpath.com/oauth/access_token'
    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'grant_type': 'client_credentials'}
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded',
               'x-moltin-auth-store': store_id}
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def get_all_products(token, store_id):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(token, cart_id, store_id):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()
    products = []
    for product in response.json()['data']:
        products.append({'id': product['id'],
                         'name': product['name'],
                         'qty': product['quantity'],
                         'price': product['meta']['display_price']['with_tax']['unit']['formatted'],
                         'subtotal': product['meta']['display_price']['with_tax']['value']['formatted']})
    total_price = response.json()['meta']['display_price']['with_tax']['formatted']
    return products, total_price


def add_product_to_cart(token, cart_id, store_id, product_id, quantity: int):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items'
    payload = json.dumps({"data": {'id': product_id,
                                   'type': "cart_item",
                                   'quantity': quantity}})
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


def delete_product_from_cart(token, cart_id, store_id, product_id):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items/{product_id}'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("DELETE", url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


def remove_all_from_cart(token, cart_id, store_id):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response = requests.request("DELETE", url, headers=headers, data=payload)
    response.raise_for_status()
    return response


def get_product_info_by_id(token, product_id, store_id):
    url_info = f'https://useast.api.elasticpath.com/catalog/products/{product_id}'
    url_description = f'https://useast.api.elasticpath.com/pcm/products/{product_id}'
    payload = {}
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': f'{store_id}',
               'Authorization': f'Bearer {token}'}
    response_info = requests.request("GET", url_info, headers=headers, data=payload)
    response_info.raise_for_status()
    response_description = requests.request("GET", url_description, headers=headers, data=payload)
    response_description.raise_for_status()
    response = {'product_name': response_info.json()['data']['attributes']['name'],
                'product_price': response_info.json()['data']['meta']['display_price']['with_tax']['formatted'],
                'product_sku': response_info.json()['data']['attributes']['sku'],
                'product_description': response_description.json()['data']['attributes']['description']}
    return response


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
    response.raise_for_status()
    file_link = response.json()['data']['link']['href']
    return file_link


def create_customer(name, email, password, store_id, token):
    url = f'https://useast.api.elasticpath.com/v2/customers'
    payload = json.dumps({"data": {
        "type": "customer",
        "name": str(name),
        "email": str(email),
        "password": str(password)}})
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.status_code == 201


def is_token_expired(token_path, store_id):
    with open(token_path, "r") as elasticpath_token:
        token = elasticpath_token.read()
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'x-moltin-auth-store': store_id,
               'Authorization': f'Bearer {token}'}
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    return response.status_code != 200


def update_elastic_token(client_id, client_secret, store_id, token_path):
    url = 'https://useast.api.elasticpath.com/oauth/access_token'
    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'grant_type': 'client_credentials'}
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded',
               'x-moltin-auth-store': store_id}
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    token = response.json()['access_token']
    os.environ["ELASTIC_TOKEN"] = token
    '''
    with open(token_path, "w") as elasticpath_token:
        elasticpath_token.write(token)
    '''
    return os.getenv('ELASTIC_TOKEN')


def get_elasticpath_token(token_path):
    with open(token_path, "r") as elasticpath_token:
        token = elasticpath_token.read()
    return token


try:
    get_all_products(os.getenv('ELASTIC_TOKEN'), '8165a9a1-dca1-4df3-b733-e223ba60ff75')
except requests.exceptions.HTTPError:
    print('Exception', os.getenv('ELASTIC_TOKEN'))

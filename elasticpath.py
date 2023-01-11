import os
import requests
from dotenv import load_dotenv


def get_client_token(client_id, client_secret, store_id):
    url = "https://useast.api.elasticpath.com/oauth/access_token"
    payload = f'client_id={client_id}&' \
              f'client_secret={client_secret}&' \
              'grant_type=client_credentials'
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded',
               'x-moltin-auth-store': store_id}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def main():
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    store_id = os.getenv('STORE_ID')

    print(get_client_token(client_id, client_secret, store_id))


if __name__ == '__main__':
    main()

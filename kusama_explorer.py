import requests
import config

API_URL_ROOT = 'https://explorer-31.polkascan.io/kusama/api/v1/account/'
ERA_API_URL = 'https://kusama.subscan.io/api/scan/metadata'


def get_account_json(address):
    res = requests.get(API_URL_ROOT + address)
    account_info = res.json()
    return account_info['data']['attributes']


def get_era_process():
    res = requests.post(ERA_API_URL)
    metadata = res.json()
    return int(metadata['data']['eraProcess'])


def get_ksm_price():
    res = requests.post('https://kusama.subscan.io/api/scan/token')
    token_info = res.json()['data']['detail']['KSM']
    return float(token_info['price'])


def get_account_info(address):
    validator_info = get_account_json(address)
    account = address[:4] + '...' + address[-4:]
    if validator_info['has_identity']:
        account = f"📋Display name: {validator_info['identity_display']}\n💠Address: {account}"
    state = '🔥Active🔥' if validator_info['is_validator'] else '💤Waiting💤'
    balance_total = validator_info['balance_total'] / 1e12
    balance_free = validator_info['balance_free'] / 1e12
    balance_reserved = validator_info['balance_reserved'] / 1e12
    return config.STATUS_MESSAGE.format(account, state, balance_total, balance_free, balance_reserved, get_ksm_price())

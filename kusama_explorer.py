import requests
import config

API_URL_ROOT = 'https://explorer-31.polkascan.io/kusama/api/v1/account/'
ERA_API_URL = 'https://kusama.subscan.io/api/scan/metadata'
KSM_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=kusama&vs_currencies=usd&include_24hr_change=true'


def get_account_json(address):
    res = requests.get(API_URL_ROOT + address)
    account_info = res.json()
    return account_info['data']['attributes']


def get_era_process():
    res = requests.post(ERA_API_URL)
    metadata = res.json()
    return int(metadata['data']['eraProcess'])


def get_ksm_price():
    res = requests.get(KSM_PRICE_URL)
    res_json = res.json()
    token_info = res_json['kusama']
    usd_price = token_info['usd']
    usd_24h_change = token_info['usd_24h_change']
    return '{} ({:.2f}%)'.format(usd_price, usd_24h_change)


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

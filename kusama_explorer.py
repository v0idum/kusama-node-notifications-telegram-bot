import requests
import config
import logging
import json

from utils import format_balance, get_index

API_URL_ROOT = 'https://explorer-31.polkascan.io/kusama/api/v1/account/'
ERA_API_URL = 'https://kusama.subscan.io/api/scan/metadata'
KSM_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=kusama&vs_currencies=usd&include_24hr_change=true'
KSM_STATS_URL = 'https://kusama.subscan.io/api/scan/token'

log = logging.getLogger(__name__)


def get_account_json(address):
    try:
        res = requests.get(API_URL_ROOT + address, timeout=10)
        res.close()
        account_info = res.json()
        return account_info['data']['attributes']
    except requests.exceptions.ConnectionError as e:
        print(e)


def get_era_process():
    try:
        res = requests.post(ERA_API_URL, timeout=10)
        res.close()
        metadata = res.json()
        return int(metadata['data']['eraProcess'])
    except requests.exceptions.ConnectionError as e:
        print(e)


def get_ksm_stats():
    text_json = ''
    try:
        res = requests.post(KSM_STATS_URL, timeout=10)
        res.close()
        text_json = res.text
    except requests.exceptions.ConnectionError as e:
        print(e)

    if text_json.count('{') == 4:
        text_json = json.loads(text_json)
    else:
        last_brace_index = get_index(text_json, '{', 5)
        text_json = json.loads(text_json[:last_brace_index])

    ksm_info = text_json['data']['detail']['KSM']

    total = format_balance(ksm_info['total_issuance'])
    available = format_balance(ksm_info['available_balance'])
    locked = format_balance(ksm_info['locked_balance'])

    era = f'{get_era_process()}/{config.ERA}'

    price = f'{float(ksm_info["price"]):.2f}'
    price_change = f'{float(ksm_info["price_change"]):.2%}'

    return config.KSM_STATS.format(total, available, locked, era, price, price_change)


def get_account_info(address):
    validator_info = get_account_json(address)
    account = address[:4] + '...' + address[-4:]
    if validator_info['has_identity']:
        account = f"📋Display name: {validator_info['identity_display']}\n💠Address: {account}"
    state = '🔥Active🔥' if validator_info['is_validator'] else '💤Waiting💤'
    balance_total = format_balance(validator_info['balance_total'], 2)
    balance_free = format_balance(validator_info['balance_free'], 2)
    balance_reserved = format_balance(validator_info['balance_reserved'], 2)
    return config.STATUS_MESSAGE.format(account, state, balance_total, balance_free, balance_reserved)

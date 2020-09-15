import requests
import config
import logging

from utils import format_balance

API_URL_ROOT = 'https://explorer-31.polkascan.io/kusama/api/v1/account/'
ERA_API_URL = 'https://kusama.subscan.io/api/scan/metadata'
KSM_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=kusama&vs_currencies=usd&include_24hr_change=true'
KSM_STATS_URL = 'https://kusama.subscan.io/api/scan/token'


log = logging.getLogger(__name__)


def get_account_json(address):
    res = requests.get(API_URL_ROOT + address)
    account_info = res.json()
    return account_info['data']['attributes']


def get_era_process():
    res = requests.post(ERA_API_URL)
    log.info('ERA:')
    log.info(res.text)
    metadata = res.json()
    return int(metadata['data']['eraProcess'])


def get_ksm_stats():
    res = requests.post(KSM_STATS_URL)
    log.info('KSM stats:')
    log.info(res.text)
    res_json = res.json()
    ksm_info = res_json['data']['detail']['KSM']

    total = format_balance(ksm_info['total_issuance'])
    available = format_balance(ksm_info['available_balance'])
    locked = format_balance(ksm_info['locked_balance'])

    era = f'{get_era_process()}/{config.ERA}'

    price = f'{float(ksm_info["price"]):.2f}'
    price_change = f'{float(ksm_info["price_change"]):.2%}'

    return config.KSM_STATS.format(total, available, locked, era, price, price_change)


# def get_ksm_price():
#     res = requests.get(KSM_PRICE_URL)
#     log.info('KSM price:')
#     log.info(res.text)
#     res_json = res.json()
#     token_info = res_json['kusama']
#     usd_price = token_info['usd']
#     usd_24h_change = token_info['usd_24h_change']
#     return '{} ({:.2f}%)'.format(usd_price, usd_24h_change)


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

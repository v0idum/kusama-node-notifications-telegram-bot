import aiohttp
import asyncio
import config
import logging
import json

from utils import format_balance, get_index

API_URL_ROOT = 'https://explorer-31.polkascan.io/kusama/api/v1/account/'
ERA_API_URL = 'https://kusama.subscan.io/api/scan/metadata'
TOKEN_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=polkadot&vs_currencies=usd&include_24hr_change=true'
KSM_STATS_URL = 'https://kusama.subscan.io/api/scan/token'

log = logging.getLogger(__name__)


async def get_account_json(session: aiohttp.ClientSession, address: str) -> dict:
    async with session.get(API_URL_ROOT + address) as response:
        account_info = await response.json()
        return account_info['data']['attributes']


async def get_era_process(session: aiohttp.ClientSession = None) -> int:
    close_after_finish = False
    if session is None:
        session = aiohttp.ClientSession()
        close_after_finish = True

    async with session.post(ERA_API_URL) as response:
        metadata = await response.json()

    if close_after_finish:
        await session.close()

    return int(metadata['data']['eraProcess'])


async def get_polkadot_price(session: aiohttp.ClientSession) -> tuple:
    async with session.get(TOKEN_PRICE_URL) as response:
        res = await response.json()
        polkadot = res['polkadot']
        return polkadot['usd'], f"{polkadot['usd_24h_change']:.2f}%"


async def ksm_stats(session) -> str:
    async with session.post(KSM_STATS_URL) as response:
        text_json = await response.text()
        return text_json


async def get_stats() -> str:
    session = aiohttp.ClientSession()

    results = await asyncio.gather(
        ksm_stats(session),
        get_era_process(session),
        get_polkadot_price(session),
    )
    await session.close()

    text_json = results[0]

    if text_json.count('{') == 4:
        text_json = json.loads(text_json)
    else:
        last_brace_index = get_index(text_json, '{', 5)
        text_json = json.loads(text_json[:last_brace_index])

    ksm_info = text_json['data']['detail']['KSM']

    total = format_balance(ksm_info['total_issuance'])
    available = format_balance(ksm_info['available_balance'])
    locked = format_balance(ksm_info['locked_balance'])

    era = f'{results[1]}/{config.ERA}'

    ksm_price = f'{float(ksm_info["price"]):.2f}'
    ksm_price_change = f'{float(ksm_info["price_change"]):.2%}'

    dot_price, dot_price_change = results[2]

    return config.KSM_STATS.format(total, available, locked, era, ksm_price, ksm_price_change, dot_price, dot_price_change)


async def get_account_info(session: aiohttp.ClientSession, address: str) -> str:
    validator_info = await get_account_json(session, address)
    account = address[:4] + '...' + address[-4:]
    if validator_info['has_identity']:
        account = f"📋Display name: {validator_info['identity_display']}\n💠Address: {account}"
    state = '🔥Active🔥' if validator_info['is_validator'] else '💤Waiting💤'
    balance_total = format_balance(validator_info['balance_total'], 2)
    balance_free = format_balance(validator_info['balance_free'], 2)
    balance_reserved = format_balance(validator_info['balance_reserved'], 2)
    return config.STATUS_MESSAGE.format(account, state, balance_total, balance_free, balance_reserved)

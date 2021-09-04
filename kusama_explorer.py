import asyncio
import json
import logging

import aiohttp
from aiohttp import ContentTypeError

import config
from utils import format_balance, get_index

ACCOUNT_INFO_URL = 'https://polkadot.api.subscan.io/api/v2/scan/search'
ERA_API_URL = 'https://polkadot.api.subscan.io/api/scan/metadata'
KSM_STATS_URL = 'https://polkadot.api.subscan.io/api/scan/token'
VALIDATOR_RANK_URL = 'https://polkadot.w3f.community/candidate/'

log = logging.getLogger(__name__)


async def get_validator_rank(session: aiohttp.ClientSession, address: str):
    try:
        async with session.get(VALIDATOR_RANK_URL + address) as response:
            details = await response.json()
            return details['rank']
    except ContentTypeError:
        return '-'
    except Exception as e:
        log.error(e)
        return '-'


async def get_account_json(session: aiohttp.ClientSession, address: str):
    try:
        async with session.post(ACCOUNT_INFO_URL, headers={'X-API-Key': config.API_KEY}, json={'key': address, 'row': 1, 'page': 0}) as response:
            account_info = await response.json()
            return account_info['data']['account']
    except Exception as e:
        log.error(f'Error during fetching {address} account info', exc_info=e)


async def get_era_process(session: aiohttp.ClientSession = None) -> int:
    close_after_finish = False
    if session is None:
        session = aiohttp.ClientSession(trust_env=True)
        close_after_finish = True

    async with session.post(ERA_API_URL, headers={'X-API-Key': config.API_KEY}) as response:
        metadata = await response.json()

    if close_after_finish:
        await session.close()

    return int(metadata['data']['eraProcess'])


async def polkadot_stats(session) -> str:
    async with session.post(KSM_STATS_URL, headers={'X-API-Key': config.API_KEY}) as response:
        text_json = await response.text()
        return text_json


async def get_stats() -> str:
    session = aiohttp.ClientSession()

    results = await asyncio.gather(
        polkadot_stats(session),
        get_era_process(session)
    )
    await session.close()

    text_json = results[0]

    if text_json.count('{') == 4:
        text_json = json.loads(text_json)
    else:
        last_brace_index = get_index(text_json, '{', 5)
        text_json = json.loads(text_json[:last_brace_index])

    dot_info = text_json['data']['detail']['DOT']

    total = format_balance(dot_info['total_issuance'])
    available = format_balance(dot_info['available_balance'])
    locked = format_balance(dot_info['locked_balance'])

    era = f'{results[1]}/{config.ERA}'

    dot_price = f'{float(dot_info["price"]):.2f}'
    dot_price_change = f'{float(dot_info["price_change"]):.2%}'

    return config.DOT_STATS.format(total, available, locked, era, dot_price, dot_price_change)


async def get_account_info(session: aiohttp.ClientSession, address: str):
    results = await asyncio.gather(
        get_account_json(session, address),
        get_validator_rank(session, address)
    )
    validator_info = results[0]
    validator_rank = results[1]

    if not validator_info:
        return
    account = address[:4] + '...' + address[-4:]

    if validator_info['account_display']['display']:
        account = f"📋Display name: {validator_info['account_display']['display']}\n💠Address: {account}"

    state = '🔥Active🔥' if validator_info['role'] == 'validator' else '💤Waiting💤'
    balance = validator_info['balance']
    reserved = format_balance(validator_info['reserved'], 2)
    locked = validator_info['balance_lock']
    return config.STATUS_MESSAGE.format(account, validator_rank, state, balance, reserved, locked)

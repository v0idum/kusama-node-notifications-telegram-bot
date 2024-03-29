import asyncio
import json
import logging
from json import JSONDecodeError

import aiohttp
from aiohttp import ContentTypeError

import config
from utils import format_balance, get_index

ACCOUNT_INFO_URL = 'https://kusama.api.subscan.io/api/v2/scan/search'
ERA_API_URL = 'https://kusama.api.subscan.io/api/scan/metadata'
TOKEN_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=polkadot&vs_currencies=usd&include_24hr_change=true'
KSM_STATS_URL = 'https://kusama.api.subscan.io/api/scan/token'
VALIDATOR_RANK_URL = 'https://kusama.w3f.community/candidate/'

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
        async with session.post(ACCOUNT_INFO_URL, headers={'X-API-Key': config.API_KEY},
                                json={'key': address, 'row': 1, 'page': 0}) as response:
            account_info = await response.json()
            print(account_info)
            return account_info['data']['account']
    except Exception as e:
        log.error(f'Error during fetching {address} account info', exc_info=e)


async def get_era_process(session: aiohttp.ClientSession = None) -> int:
    close_after_finish = False
    if session is None:
        session = aiohttp.ClientSession(trust_env=True)
        close_after_finish = True

    async with session.post(ERA_API_URL, headers={'X-API-Key': config.API_KEY}) as response:
        try:
            metadata = await response.json()
        except JSONDecodeError:
            era_text = await response.text()
            log.exception(f'Era process {era_text}')
            last_brace_index = get_index(era_text, '{', 3)
            metadata = json.loads(era_text[:last_brace_index])
    if close_after_finish:
        await session.close()

    return int(metadata['data']['eraProcess'])


async def get_polkadot_price(session: aiohttp.ClientSession) -> tuple:
    async with session.get(TOKEN_PRICE_URL) as response:
        res = await response.json()
        polkadot = res['polkadot']
        return polkadot['usd'], f"{polkadot['usd_24h_change']:.2f}%"


async def ksm_stats(session) -> str:
    async with session.post(KSM_STATS_URL, headers={'X-API-Key': config.API_KEY}) as response:
        try:
            stats = await response.json()
        except JSONDecodeError:
            stats_text = await response.text()
            log.exception(f'Ksm stats {stats_text}')
            last_brace_index = get_index(stats_text, '{', 5)
            stats = json.loads(stats_text[:last_brace_index])
        return stats


async def get_stats() -> str:
    session = aiohttp.ClientSession()

    results = await asyncio.gather(
        ksm_stats(session),
        get_era_process(session),
        get_polkadot_price(session),
    )
    await session.close()

    token_stats = results[0]

    ksm_info = token_stats['data']['detail']['KSM']

    total = format_balance(ksm_info['total_issuance'])
    locked = format_balance(ksm_info['bonded_locked_balance'])
    available = format_balance(int(ksm_info['total_issuance']) - int(ksm_info['bonded_locked_balance']))

    era = f'{results[1]}/{config.ERA}'

    ksm_price = f'{float(ksm_info["price"]):.2f}'
    ksm_price_change = f'{float(ksm_info["price_change"]):.2%}'

    dot_price, dot_price_change = results[2]

    return config.KSM_STATS.format(total, available, locked, era, ksm_price, ksm_price_change, dot_price,
                                   dot_price_change)


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

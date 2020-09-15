import config
import logging
import kusama_explorer
import asyncio

from sqlighter import SQLighter
from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import trim_address

logging.basicConfig(level=logging.INFO, filename='logs.log')

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

db = SQLighter('db.db')


def home_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    add_validator_btn = KeyboardButton(config.ADD_VALIDATOR)
    remove_validator_btn = KeyboardButton(config.REMOVE_VALIDATOR)
    status_btn = KeyboardButton(config.STATUS)
    stats_btn = KeyboardButton(config.STATS)
    donate_btn = KeyboardButton(config.DONATE)
    keyboard.add(add_validator_btn, remove_validator_btn, status_btn, stats_btn, donate_btn)
    return keyboard


@dp.message_handler(lambda message: message.from_user.id in config.ADMINS, commands='users')
async def get_users(message: types.Message):
    await message.answer(db.get_users())


@dp.message_handler(filters.CommandStart())
async def welcome(message: types.Message):
    await message.answer(config.WELCOME_MESSAGE, reply_markup=home_kb())


@dp.message_handler(filters.Text(config.ADD_VALIDATOR))
async def add_validator_handler(message: types.Message):
    await message.answer('Enter a Validator account address:', reply_markup=home_kb())


@dp.message_handler(text=config.REMOVE_VALIDATOR)
async def send_validator_removing_kb(message: types.Message):
    validators = db.get_validators_by_user(message.from_user.id)
    response = 'You have no validators to remove!'
    markup = None
    if validators:
        markup = InlineKeyboardMarkup()
        buttons = (InlineKeyboardButton(trim_address(*address), callback_data=address[0]) for address in validators)
        markup.add(*buttons)
        response = 'Tap the address you want to remove:'
    await message.answer(response, reply_markup=markup)


@dp.callback_query_handler()
async def remove_selected_validator(query: types.CallbackQuery):
    db.delete_validator_by_user(query.from_user.id, query.data)
    await query.answer('Success')
    await query.message.edit_text('Removed.')


@dp.message_handler(filters.Text([config.STATUS]))
async def get_validators_status(message: types.Message):
    validators = db.get_validators_by_user(message.from_user.id)
    for validator in validators:
        await message.answer(kusama_explorer.get_account_info(*validator), reply_markup=home_kb())


@dp.message_handler(text=config.STATS)
async def get_ksm_stats(message: types.Message):
    await message.answer(kusama_explorer.get_ksm_stats(), reply_markup=home_kb())


@dp.message_handler(filters.Text([config.DONATE]))
async def process_donate(message: types.Message):
    await message.answer(config.DONATE_MESSAGE)
    await message.answer(config.DONATE_ADDRESS, reply_markup=home_kb())


@dp.message_handler()
async def validator_address_handler(message: types.Message):
    response = '️️✔️Validator added successfully!'
    try:
        validator_info = kusama_explorer.get_account_json(message.text)
        db.add_validator_to_user(message.from_user.id, validator_info['address'])
        logging.log(logging.INFO,
                    f'{message.from_user.id} {message.from_user.username} added {validator_info["address"]}')
    except KeyError:
        response = '❌Invalid address! Try again.'
    await message.answer(response, reply_markup=home_kb())


async def notify_users():
    validators = db.get_user_validators()
    first = validators[0]
    temp_address = first[1]
    validator_info = kusama_explorer.get_account_info(temp_address)
    for validator in validators:
        user_id, address = validator
        if address != temp_address:
            temp_address = address
            validator_info = kusama_explorer.get_account_info(temp_address)
        await bot.send_message(user_id, validator_info)
        await asyncio.sleep(0.04)


async def monitor_era_progress():
    era_process = kusama_explorer.get_era_process()
    pause = (config.ERA - era_process) * config.BLOCK_TIME
    while True:
        logging.log(logging.INFO, f'Sleeping on {pause} sec, era {era_process}')
        await asyncio.sleep(pause)
        era_current = kusama_explorer.get_era_process()
        pause = (config.ERA - era_current) * config.BLOCK_TIME
        if era_process > era_current:
            await notify_users()
            logging.log(logging.INFO, f'New era, era current: {era_current}')
        elif era_process == era_current:
            pause = 30
        era_process = era_current


if __name__ == '__main__':
    dp.loop.create_task(monitor_era_progress())
    executor.start_polling(dp, skip_updates=True)

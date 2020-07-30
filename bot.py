import config
import logging
import kusama_explorer
import asyncio

from sqlighter import SQLighter
from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

db = SQLighter('db.db')

keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
add_validator_btn = KeyboardButton(config.ADD_VALIDATOR)
status_btn = KeyboardButton(config.STATUS)
era_btn = KeyboardButton(config.ERA_PROCESS)
donate_btn = KeyboardButton(config.DONATE)
keyboard.add(add_validator_btn)
keyboard.add(status_btn)
keyboard.add(era_btn)
keyboard.add(donate_btn)


@dp.message_handler(filters.CommandStart())
async def welcome(message: types.Message):
    await message.answer(config.WELCOME_MESSAGE, reply_markup=keyboard)


@dp.message_handler(filters.Text(config.ADD_VALIDATOR))
async def add_validator_handler(message: types.Message):
    await message.answer('Enter a Validator account address:')


@dp.message_handler(filters.Text([config.STATUS]))
async def get_validators_status(message: types.Message):
    validators = db.get_validators_by_user(message.from_user.id)
    for validator in validators:
        await message.answer(kusama_explorer.get_account_info(*validator))


@dp.message_handler(filters.Text([config.ERA_PROCESS]))
async def get_validators_status(message: types.Message):
    await message.answer(f'🔄Era: {kusama_explorer.get_era_process()}/{config.ERA}')


@dp.message_handler(filters.Text([config.DONATE]))
async def get_validators_status(message: types.Message):
    await message.answer(config.DONATE_MESSAGE)
    await message.answer(config.DONATE_ADDRESS)


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
    await message.answer(response)


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

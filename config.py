import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMINS = os.getenv('ADMINS').split(' ')
DONATE_ADDRESS = os.getenv('DONATE_ADDRESS')

WELCOME_MESSAGE = 'Hello! I can show you details about the state of any Kusama validator. Just send me the validator address.'

STATUS_MESSAGE = '''{}
⭐Rank: {}
📜Current validator state: {}
💰Balance: {} KSM
🏦Reserved: {} KSM
🔒Locked: {} KSM
'''

KSM_STATS = '''🏦Total issuance: {}
💸Transferable: {}
🔐Locked: {}
🔄Era: {}
📈KSM: 💲{} ({})
📈DOT: 💲{} ({})
'''

ADD_VALIDATOR = '➕Add Validator'
REMOVE_VALIDATOR = '❌Remove Validator'
STATUS = 'ℹ️Status'
STATS = '📊Stats'
DONATE = '💚Donate'

DONATE_MESSAGE = '🍺Support me by sending a donation to my KSM address😄'

ERA = 3600
BLOCK_TIME = 6

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN_TELEGRAM_BOT = os.environ.get('TOKEN_TELEGRAM_BOT')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
PROXY_URL = os.environ.get('PROXY_URL')
QUESTIONS_FILE = os.environ.get('QUESTIONS_FILE')
TOKEN_VK_BOT = os.environ.get('TOKEN_VK_BOT')
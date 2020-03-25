import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
PROXY_URL = os.environ.get('PROXY_URL')
QUESTIONS_FILE = os.environ.get('QUESTIONS_FILE')
VK_TOKEN = os.environ.get('VK_TOKEN')

NEW_QUESTION, SOLUTION_ATTEMPT, SURRENDER, NOT_CURRENTLY_ANSWER = range(4)

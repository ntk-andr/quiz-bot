#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import redis

from questions import get_one_question
import os
from dotenv import load_dotenv

load_dotenv()

question_count = 0

TOKEN_TELEGRAM_BOT = os.environ.get('TOKEN_TELEGRAM_BOT')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
PROXY_URL = os.environ.get('PROXY_URL')
QUESTIONS_FILE = os.environ.get('QUESTIONS_FILE')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
)
logger = logging.getLogger(__name__)


def get_keyboard():
    keyboard = [['Новый вопрос', 'Сдаться'],
                ['Мой счет']]

    return ReplyKeyboardMarkup(keyboard)


def start(bot, update):
    update.message.reply_text('Начинаем, «Новый вопрос»!!!', reply_markup=get_keyboard())


def handler_message(bot, update):
    global question_count

    if update.message.text == 'Новый вопрос':
        filename = QUESTIONS_FILE
        question = get_one_question(filename)
        message_text = question['question']
        answer_text = question['answer']
        chat_id = update.message.chat.id
        question_count = len(list(r.scan_iter(f'{chat_id}_question_*'))) + 1
        set_key = f'{chat_id}_question_{question_count}'
        set_value = json.dumps({
            'question_count': question_count,
            'question': message_text,
            'answer': answer_text,
        })
        r.set(set_key, set_value)
    else:
        chat_id = update.message.chat.id
        answer_user = update.message.text.lower()
        question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
        set_key = f'{chat_id}_question_{question_count}'
        set_value = json.loads(r.get(set_key).decode())
        answer = set_value['answer']
        currently_answer = answer.rsplit('.')[0].rsplit('(')[0].strip().lower()

        if currently_answer == answer_user:
            message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
            set_value['is_currently'] = 'true'
        else:
            message_text = 'Неправильно... Попробуешь ещё раз?'
            set_value['is_currently'] = 'false'

        set_value['answer_user'] = answer_user
        set_value = json.dumps(set_value)
        r.set(set_key, set_value)

    update.message.reply_text(message_text)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    if PROXY_URL:
        request_kwargs = {'proxy_url': PROXY_URL}
        updater = Updater(token=TOKEN_TELEGRAM_BOT, request_kwargs=request_kwargs)
    else:
        updater = Updater(token=TOKEN_TELEGRAM_BOT)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handler_message))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
import redis

from questions import get_one_question
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN_TELEGRAM_BOT = os.environ.get('TOKEN_TELEGRAM_BOT')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
PROXY_URL = os.environ.get('PROXY_URL')
QUESTIONS_FILE = os.environ.get('QUESTIONS_FILE')

NEW_QUESTION, SOLUTION_ATTEMPT = range(2)

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
    return NEW_QUESTION


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def handle_new_question_request(bot, update):
    question = get_one_question(QUESTIONS_FILE)
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
    update.message.reply_text(message_text)
    return SOLUTION_ATTEMPT


def handle_solution_attempt(bot, update):
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
        result = NEW_QUESTION
    else:
        message_text = 'Неправильно... Попробуешь ещё раз?'
        set_value['is_currently'] = 'false'
        result = SOLUTION_ATTEMPT

    set_value['answer_user'] = answer_user
    set_value = json.dumps(set_value)
    r.set(set_key, set_value)

    update.message.reply_text(message_text)
    return result


def cancel(bot, update):
    update.message.reply_text('cancel')
    return ConversationHandler.END


def main():
    if PROXY_URL:
        request_kwargs = {'proxy_url': PROXY_URL}
        updater = Updater(token=TOKEN_TELEGRAM_BOT, request_kwargs=request_kwargs)
    else:
        updater = Updater(token=TOKEN_TELEGRAM_BOT)

    dp = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION: [RegexHandler('^(Новый вопрос)$', handle_new_question_request)],
            SOLUTION_ATTEMPT: [MessageHandler(Filters.text, handle_solution_attempt)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conversation_handler)
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)
    main()

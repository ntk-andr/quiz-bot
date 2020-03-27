from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
import redis

from questions import get_question, read_file, get_result, get_message_for_surrender, get_message_for_new_question

from settings import QUESTIONS_FILE, PROXY_URL, TELEGRAM_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, \
    SOLUTION_ATTEMPT, NEW_QUESTION


def get_keyboard():
    keyboard = [['Новый вопрос', 'Сдаться'],
                ['Мой счет']]

    return ReplyKeyboardMarkup(keyboard)


def handler_start(bot, update):
    message_text = 'Начинаем, нажмите «Новый вопрос» для начала викторины.\n /cancel - для отмены'
    update.message.reply_text(message_text, reply_markup=get_keyboard())
    return NEW_QUESTION


def error(bot, update, error):
    message = f'Update {update} caused error {error}'
    logger.warning(message)


def handle_new_question_request(bot, update):
    """Новый вопрос."""
    question = get_question(read_file(QUESTIONS_FILE))
    chat_id = update.message.chat.id
    message_text = get_message_for_new_question(chat_id, question, r)
    update.message.reply_text(message_text)
    return SOLUTION_ATTEMPT


def handle_solution_attempt(bot, update):
    """Попытка ответить"""
    chat_id = update.message.chat.id
    answer_user = update.message.text
    result = get_result(chat_id, answer_user, r)

    update.message.reply_text(result['message_text'])
    return NEW_QUESTION if result['fields']['is_currently'] else SOLUTION_ATTEMPT


def surrender(bot, update):
    """Сдаться"""
    chat_id = update.message.chat.id
    message_text = get_message_for_surrender(chat_id, r)
    update.message.reply_text(message_text)
    return NEW_QUESTION


def handler_cancel(bot, update):
    """Завершение викторины"""
    update.message.reply_text('Викторина завершена\n/start - для начала')
    return ConversationHandler.END


def main():
    if PROXY_URL:
        request_kwargs = {'proxy_url': PROXY_URL}
        updater = Updater(token=TELEGRAM_TOKEN, request_kwargs=request_kwargs)
    else:
        updater = Updater(token=TELEGRAM_TOKEN)

    dp = updater.dispatcher

    handler_conversation = ConversationHandler(
        entry_points=[CommandHandler('start', handler_start)],
        states={
            NEW_QUESTION: [RegexHandler('^Новый вопрос$', handle_new_question_request)],
            SOLUTION_ATTEMPT: [
                RegexHandler('^Сдаться$', surrender),
                RegexHandler('^Новый вопрос$', handle_new_question_request),
                MessageHandler(Filters.text, handle_solution_attempt),
            ],
        },
        fallbacks=[CommandHandler('cancel', handler_cancel)]
    )

    dp.add_handler(handler_conversation)

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)
    main()

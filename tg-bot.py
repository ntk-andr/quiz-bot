from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
import redis

from questions import get_question, read_quiz_file, get_result, get_message_for_surrender, switch_to_next_question, \
    get_chat_id

from settings import QUESTIONS_FILE, PROXY_URL, TELEGRAM_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, \
    SOLUTION_ATTEMPT, NEW_QUESTION, POSTFIX_TELEGRAM

logger = logging.getLogger(__file__)


def get_keyboard():
    keyboard = [['Новый вопрос', 'Сдаться'],
                ['Мой счет']]
    return ReplyKeyboardMarkup(keyboard)


def start_quiz(bot, update):
    message_text = 'Начинаем, нажмите «Новый вопрос» для начала викторины.\n /cancel - для отмены'
    update.message.reply_text(message_text, reply_markup=get_keyboard())
    return NEW_QUESTION


def error(bot, update, error):
    message = f'Update {update} caused error {error}'
    logger.warning(message)


def get_new_question(bot, update):
    """Новый вопрос."""
    question = get_question(read_quiz_file(QUESTIONS_FILE))
    chat_id = get_chat_id(update.message.chat.id, POSTFIX_TELEGRAM)
    message_text = switch_to_next_question(chat_id, question, r)
    update.message.reply_text(message_text)
    return SOLUTION_ATTEMPT


def answer_the_question(bot, update):
    """Попытка ответить."""
    chat_id = get_chat_id(update.message.chat.id, POSTFIX_TELEGRAM)
    answer_of_user = update.message.text
    result = get_result(chat_id, answer_of_user, r)

    update.message.reply_text(result['message_text'])
    return NEW_QUESTION if result['fields']['is_correct'] else SOLUTION_ATTEMPT


def get_the_correct_answer(bot, update):
    """Сдаться."""
    chat_id = get_chat_id(update.message.chat.id, POSTFIX_TELEGRAM)
    message_text = get_message_for_surrender(chat_id, r)
    update.message.reply_text(message_text)
    return NEW_QUESTION


def cancel_quiz(bot, update):
    """Завершение викторины."""
    update.message.reply_text('Викторина завершена\n/start - для начала')
    return ConversationHandler.END


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.setLevel(logging.WARNING)

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)

    if PROXY_URL:
        request_kwargs = {'proxy_url': PROXY_URL}
        updater = Updater(token=TELEGRAM_TOKEN, request_kwargs=request_kwargs)
    else:
        updater = Updater(token=TELEGRAM_TOKEN)
    dp = updater.dispatcher
    handler_conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start_quiz)],
        states={
            NEW_QUESTION: [RegexHandler('^Новый вопрос$', get_new_question)],
            SOLUTION_ATTEMPT: [
                RegexHandler('^Сдаться$', get_the_correct_answer),
                RegexHandler('^Новый вопрос$', get_new_question),
                MessageHandler(Filters.text, answer_the_question),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_quiz)]
    )
    dp.add_handler(handler_conversation)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

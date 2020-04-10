import random

import redis
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from questions import get_question, read_quiz_file, get_result, get_message_for_surrender, switch_to_next_question, \
    get_chat_id

from settings import VK_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, QUESTIONS_FILE, POSTFIX_VK


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)
    return keyboard.get_keyboard()


def start_quiz(event, vk_api):
    """Приветственное сообщение."""
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message='Приветствую тебя в нашей викторине! Для начала нажми «Новый вопрос»',
    )


def get_new_question(event, vk_api):
    """Новый вопрос."""
    question = get_question(read_quiz_file(QUESTIONS_FILE))
    chat_id = get_chat_id(event.user_id, POSTFIX_VK)
    message_text = switch_to_next_question(chat_id, question, r)
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def answer_the_question(event, vk_api):
    """Попытка ответа."""
    chat_id = get_chat_id(event.user_id, POSTFIX_VK)
    answer_of_user = event.text
    result = get_result(chat_id, answer_of_user, r)

    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=result['message_text'],
    )


def get_the_correct_answer(event, vk_api):
    """Сдаться."""
    chat_id = get_chat_id(event.user_id, POSTFIX_VK)
    message_text = get_message_for_surrender(chat_id, r)
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


if __name__ == "__main__":
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Привет':
                start_quiz(event, vk_api)
            elif event.text == 'Сдаться':
                get_the_correct_answer(event, vk_api)
            elif event.text == 'Новый вопрос':
                get_new_question(event, vk_api)
            else:
                answer_the_question(event, vk_api)

import random

import redis
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from questions import get_question, read_file, get_result, get_message_for_surrender, get_message_for_new_question

from settings import VK_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, QUESTIONS_FILE


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)
    return keyboard.get_keyboard()


def handler_welcome_message(event, vk_api):
    """Приветственное сообщение."""
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message='Приветствую тебя в нашей викторине! Для начала нажми «Новый вопрос»',
    )


def handle_new_question_request(event, vk_api):
    """Новый вопрос."""
    question = get_question(read_file(QUESTIONS_FILE))
    chat_id = event.user_id
    message_text = get_message_for_new_question(chat_id, question, r)
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def handle_solution_attempt(event, vk_api):
    """Попытка ответа."""
    chat_id = event.user_id
    answer_user = event.text
    result = get_result(chat_id, answer_user, r)

    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=result['message_text'],
    )


def surrender(event, vk_api):
    """Сдаться."""
    chat_id = event.user_id
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
                handler_welcome_message(event, vk_api)
            elif event.text == 'Сдаться':
                surrender(event, vk_api)
            elif event.text == 'Новый вопрос':
                handle_new_question_request(event, vk_api)
            else:
                handle_solution_attempt(event, vk_api)

import random

import redis
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from questions import get_question, read_file

from settings import VK_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, QUESTIONS_FILE
from utils import save_in_redis


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
    chat_id = event.user_id
    question = get_question(read_file(QUESTIONS_FILE))
    message_text = question['question']
    answer_text = question['answer']
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*'))) + 1
    set_key = f'{chat_id}_question_{question_count}'
    set_value = {
        'question_count': question_count,
        'question': message_text,
        'answer': answer_text,
    }
    save_in_redis(set_key, set_value, r)
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def handle_solution_attempt(event, vk_api):
    """Попытка ответа."""
    set_value = dict()
    chat_id = event.user_id
    answer_user = event.text
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    answer = r.hget(set_key, 'answer').decode()
    currently_answer = answer.rsplit('.')[0].rsplit('(')[0].strip().lower()
    set_value['answer_user'] = answer_user
    message_text = ''
    if answer_user != 'Сдаться':
        message_text = 'Неправильно... Попробуешь ещё раз?'
        set_value['is_currently'] = 'false'
    if currently_answer == answer_user:
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        set_value['is_currently'] = 'true'
    save_in_redis(set_key, set_value, r)
    return vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def surrender(event, vk_api):
    """Сдаться."""
    chat_id = event.user_id
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    answer = r.hget(set_key, 'answer').decode()
    message_text = f"Правильный ответ: {answer}\nЧтобы продолжить нажми «Новый вопрос»"
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

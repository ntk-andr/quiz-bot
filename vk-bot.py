import json

import random

import redis
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from questions import get_one_question

from settings import QUESTIONS_FILE, VK_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)
    return keyboard.get_keyboard()


def handler_message(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=event.text,
    )


def handle_new_question_request(event, vk_api):
    chat_id = event.user_id
    question = get_one_question(QUESTIONS_FILE)
    message_text = question['question']
    answer_text = question['answer']
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*'))) + 1
    set_key = f'{chat_id}_question_{question_count}'
    set_value = json.dumps({
        'question_count': question_count,
        'question': message_text,
        'answer': answer_text,
    })
    r.set(set_key, set_value)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def handle_solution_attempt(event, vk_api):
    chat_id = event.user_id
    answer_user = event.text
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    set_value = json.loads(r.get(set_key).decode())
    answer = set_value['answer']
    currently_answer = answer.rsplit('.')[0].rsplit('(')[0].strip().lower()
    set_value['answer_user'] = answer_user
    message_text = ''
    if event.text != 'Сдаться':
        message_text = 'Неправильно... Попробуешь ещё раз?'
        set_value['is_currently'] = 'false'

    if currently_answer == answer_user:
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        set_value['is_currently'] = 'true'

    set_value = json.dumps(set_value)
    r.set(set_key, set_value)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=get_keyboard(),
        message=message_text,
    )


def surrender(event, vk_api):
    chat_id = event.user_id
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    set_value = json.loads(r.get(set_key).decode())
    message_text = f"Правильный ответ: {set_value['answer']}\nЧтобы продолжить нажми «Новый вопрос»"
    vk_api.messages.send(
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
            if event.text == 'Сдаться':
                surrender(event, vk_api)
            if event.text == 'Новый вопрос':
                handle_new_question_request(event, vk_api)
            else:
                handle_solution_attempt(event, vk_api)

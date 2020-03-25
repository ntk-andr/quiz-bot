import random

import redis


def get_result(chat_id, answer_user, r):
    """получаем результат"""
    set_value = dict()
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    answer = r.hget(set_key, 'answer').decode()
    currently_answer = answer.rsplit('.')[0].rsplit('(')[0].strip().lower()
    set_value['answer_user'] = answer_user
    message_text = ''
    if answer_user != 'Сдаться':
        message_text = 'Неправильно... Попробуешь ещё раз?'
        set_value['is_currently'] = 'false'
    elif answer_user == currently_answer:
        message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        set_value['is_currently'] = 'true'
    save_in_redis(set_key, set_value, r)
    return {
        'set_key': set_key,
        'set_value': set_value,
        'message_text': message_text
    }


def get_message_for_new_question(chat_id, question, r):
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
    print('Правильный ответ', answer_text)
    return message_text


def get_message_for_surrender(chat_id, r):
    question_count = len(list(r.scan_iter(f'{chat_id}_question_*')))
    set_key = f'{chat_id}_question_{question_count}'
    answer = r.hget(set_key, 'answer').decode()
    return f"Правильный ответ: {answer}\nЧтобы продолжить нажми «Новый вопрос»"


def get_text(text: str) -> str:
    symbol_position = text.find(':') + 1
    return text.replace('\n', ' ')[symbol_position:].strip()


def read_file(filename: str, encoding='KOI8-R') -> str:
    with open(filename, 'r', encoding=encoding) as file:
        return file.read()


def get_questions(text: str) -> dict:
    quiz = text.split('\n\n\n')
    answer = question = ''
    questions = dict()
    for quiz_question in quiz:
        for question_item in quiz_question.split('\n\n'):
            if 'Вопрос' in question_item:
                question = get_text(question_item)
            if 'Ответ' in question_item:
                answer = get_text(question_item)

            if answer and question:
                questions[question] = answer

    return questions


def get_question(text: str) -> dict:
    questions = list(get_questions(text).items())
    question, answer = random.choice(questions)

    return {
        'question': question,
        'answer': answer
    }


def save_in_redis(set_key: str, set_value: dict, r: redis):
    for key in set_value:
        value = str(set_value[key])
        r.hset(set_key, key, value)

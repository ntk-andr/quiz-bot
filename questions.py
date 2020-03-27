import json
import random

import redis


def get_result(chat_id, answer_user, r):
    """получаем результат"""
    question_count = get_question_count(chat_id, r)
    fields = json.loads(r.hget(chat_id, question_count))
    answer = fields['answer']
    currently_answer = answer.split('.')[0].split('(')[0].strip().lower()
    fields['answer_user'] = answer_user
    message = ''
    if answer_user != 'Сдаться':
        message = 'Неправильно... Попробуешь ещё раз?'
        fields['is_currently'] = False
    elif answer_user == currently_answer:
        message = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        fields['is_currently'] = True
    save_in_redis(chat_id, fields, r)
    return {
        'hash_key': chat_id,
        'fields': fields,
        'message_text': message
    }


def get_message_for_new_question(chat_id, question, r):
    message = question['question']
    answer = question['answer']
    fields = {
        'question': message,
        'answer': answer,
    }
    save_in_redis(chat_id, fields, r)
    return message


def get_message_for_surrender(chat_id, r):
    question_count = get_question_count(chat_id, r)
    result = json.loads(r.hget(chat_id, question_count))
    answer = result['answer']
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


def save_in_redis(hash_key, fields: dict, r: redis):
    count_questions = get_question_count(hash_key, r)
    key = 1 if count_questions == 0 else count_questions
    value = json.dumps(fields)
    r.hset(hash_key, key, value)


def get_question_count(hash_key, r):
    return len(r.hgetall(hash_key))

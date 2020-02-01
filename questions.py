import random


def get_text(text: str) -> str:
    return text.replace('\n', ' ')[text.find(':') + 1:].strip()


def read_file(filename: str, encoding='KOI8-R') -> list:
    with open(filename, 'r', encoding=encoding) as file:
        return file.read().split('\n\n\n')


def get_questions(filename: str) -> dict:
    quiz = read_file(filename)
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


def get_one_question(filename: str) -> dict:
    questions = list(get_questions(filename).items())
    choice = random.choice(questions)

    return {
        'question': choice[0],
        'answer': choice[1]
    }

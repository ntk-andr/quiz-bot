import random


def get_questions(filename: str):
    with open(filename, 'r', encoding='KOI8-R') as file:
        quiz = file.read().split('\n\n\n')
        dict_questions = dict()
        a = q = ''
        for question in quiz:
            for question_str in question.split('\n\n'):

                if 'Вопрос' in question_str:
                    q = question_str.replace('\n', ' ')[question_str.find(':') + 1:].strip()
                if 'Ответ' in question_str:
                    a = question_str.replace('\n', ' ')[question_str.find(':') + 1:].strip()

                if a and q:
                    dict_questions[q] = a

    return dict_questions


def get_one_question(filename: str):
    questions = list(get_questions(filename).items())
    choice = random.choice(questions)

    return {
        'question': choice[0],
        'answer': choice[1]
    }

# if __name__ == '__main__':
# dict_q = get_questions('questions/1vs1200.txt')
# dict_q = get_one_question('questions/1vs1200.txt')
# print(dict_q)

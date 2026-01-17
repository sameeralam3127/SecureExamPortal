import random

def generate_random_order(exam):
    question_ids = [q.id for q in exam.questions]
    random.shuffle(question_ids)

    option_order = {}
    for q in exam.questions:
        opts = ["A", "B", "C", "D"]
        random.shuffle(opts)
        option_order[q.id] = opts

    return question_ids, option_order

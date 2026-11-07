from py.validators import validate_quiz

VALID = {'text': 'Q', 'choices': ['a', 'b', 'c', 'd'], 'correct_choice_id': 2}


def test_valid():
    quiz, errors = validate_quiz(VALID)
    assert not errors and quiz['choices'][1] == {'id': 2, 'text': 'b'}


def test_invalid():
    assert validate_quiz({**VALID, 'choices': ['a']})[1]
    assert validate_quiz({**VALID, 'correct_choice_id': 5})[1]
    assert validate_quiz({**VALID, 'text': ' '})[1]

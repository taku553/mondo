import unittest

from py.validators import validate_quiz

VALID = {
    'title': 'T',
    'text': 'Q',
    'choices': ['a', 'b', 'c', 'd'],
    'correct_choice_id': 2,
    'explanation': '',
    'tags': ['歴史', '歴史'],
    'status': 'published',
}


class ValidateQuizTest(unittest.TestCase):
    def test_valid_quiz_is_normalized(self):
        quiz, errors = validate_quiz(VALID)
        self.assertEqual(errors, [])
        self.assertEqual(quiz['choices'][1], {'id': 2, 'text': 'b'})
        self.assertEqual(quiz['tags'], ['歴史'])

    def test_invalid_choices_text_and_answer_are_rejected(self):
        self.assertTrue(validate_quiz({**VALID, 'choices': ['a']})[1])
        self.assertTrue(validate_quiz({**VALID, 'correct_choice_id': 5})[1])
        self.assertTrue(validate_quiz({**VALID, 'correct_choice_id': True})[1])
        self.assertTrue(validate_quiz({**VALID, 'text': ' '})[1])

    def test_title_and_status_are_required(self):
        self.assertTrue(validate_quiz({**VALID, 'title': ''})[1])
        self.assertTrue(validate_quiz({**VALID, 'status': 'archived'})[1])

    def test_tags_are_limited(self):
        self.assertTrue(validate_quiz({**VALID, 'tags': ['a'] * 1 + ['b' * 21]})[1])
        self.assertTrue(validate_quiz({**VALID, 'tags': ['1', '2', '3', '4', '5', '6']})[1])
        self.assertTrue(validate_quiz({**VALID, 'tags': 'not-a-list'})[1])


if __name__ == '__main__':
    unittest.main()

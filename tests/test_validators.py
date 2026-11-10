import base64
import io
import unittest

from PIL import Image

from py.validators import validate_image, validate_quiz

IMAGE_PREFIX = 'data:image/jpeg;base64,'


def _jpeg(size=(800, 450), quality=80, fmt='JPEG'):
    buffer = io.BytesIO()
    Image.new('RGB', size, (200, 30, 30)).save(buffer, format=fmt, quality=quality)
    return IMAGE_PREFIX + base64.b64encode(buffer.getvalue()).decode('ascii')


QUESTION = {
    'text': 'Q',
    'choices': ['a', 'b', 'c', 'd'],
    'correct_choice_id': 2,
    'explanation': '',
}

VALID = {
    'title': 'T',
    'genre': '歴史',
    'summary': '概要',
    'questions': [QUESTION],
    'tags': ['歴史', '歴史'],
    'status': 'published',
    'image': _jpeg(),
}


class ValidateQuizTest(unittest.TestCase):
    def test_valid_quiz_is_normalized(self):
        quiz, errors = validate_quiz(VALID)
        self.assertEqual(errors, [])
        self.assertEqual(quiz['questions'][0]['choices'][1], {'id': 2, 'text': 'b'})
        self.assertEqual(quiz['tags'], ['歴史'])
        self.assertEqual(quiz['genre'], '歴史')
        self.assertNotIn('description', quiz)

    def test_up_to_twenty_questions_are_allowed(self):
        self.assertEqual(validate_quiz({**VALID, 'questions': [QUESTION] * 20})[1], [])
        self.assertTrue(validate_quiz({**VALID, 'questions': [QUESTION] * 21})[1])
        self.assertTrue(validate_quiz({**VALID, 'questions': []})[1])

    def test_invalid_choices_text_and_answer_are_rejected(self):
        bad = dict(QUESTION, choices=['a'])
        self.assertTrue(validate_quiz({**VALID, 'questions': [bad]})[1])
        self.assertTrue(validate_quiz({**VALID, 'questions': [dict(QUESTION, correct_choice_id=5)]})[1])
        self.assertTrue(validate_quiz({**VALID, 'questions': [dict(QUESTION, correct_choice_id=True)]})[1])
        self.assertTrue(validate_quiz({**VALID, 'questions': [dict(QUESTION, text=' ')]})[1])

    def test_title_genre_summary_and_status_are_required(self):
        self.assertTrue(validate_quiz({**VALID, 'title': ''})[1])
        self.assertTrue(validate_quiz({**VALID, 'genre': ''})[1])
        self.assertTrue(validate_quiz({**VALID, 'genre': 'g' * 21})[1])
        self.assertTrue(validate_quiz({**VALID, 'summary': ''})[1])
        self.assertTrue(validate_quiz({**VALID, 'summary': 's' * 101})[1])
        self.assertTrue(validate_quiz({**VALID, 'status': 'archived'})[1])

    def test_image_is_required_on_create_and_optional_on_update(self):
        self.assertTrue(validate_quiz({**VALID, 'image': None})[1])
        quiz, errors = validate_quiz({**VALID, 'image': None}, require_image=False)
        self.assertEqual(errors, [])
        self.assertIsNone(quiz['image'])

    def test_tags_are_limited(self):
        self.assertTrue(validate_quiz({**VALID, 'tags': ['a'] * 1 + ['b' * 21]})[1])
        self.assertTrue(validate_quiz({**VALID, 'tags': ['1', '2', '3', '4', '5', '6']})[1])
        self.assertTrue(validate_quiz({**VALID, 'tags': 'not-a-list'})[1])


class ValidateImageTest(unittest.TestCase):
    def test_exact_jpeg_800x450_is_accepted(self):
        encoded, errors = validate_image(_jpeg())
        self.assertEqual(errors, [])
        self.assertTrue(encoded)

    def test_wrong_size_or_format_is_rejected(self):
        self.assertTrue(validate_image(_jpeg(size=(640, 360)))[1])
        self.assertTrue(validate_image(_jpeg(fmt='PNG'))[1])
        self.assertTrue(validate_image('data:image/png;base64,AAAA')[1])
        self.assertTrue(validate_image(None)[1])

    def test_image_over_100kb_is_rejected(self):
        noisy = Image.effect_noise((800, 450), 100).convert('RGB')
        buffer = io.BytesIO()
        noisy.save(buffer, format='JPEG', quality=100)
        self.assertGreater(len(buffer.getvalue()), 100 * 1024)
        self.assertTrue(validate_image(IMAGE_PREFIX + base64.b64encode(buffer.getvalue()).decode('ascii'))[1])


if __name__ == '__main__':
    unittest.main()


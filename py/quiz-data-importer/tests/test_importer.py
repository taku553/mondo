import unittest
import os
from src.importer import load_quiz_data

class TestImporter(unittest.TestCase):

    def setUp(self):
        # 現在のテストファイルのディレクトリからの相対パスで指定
        self.test_file_path = os.path.join(
            os.path.dirname(__file__), 
            'test_data', 
            'sample_quiz.md'
        )

    def test_load_quiz_data(self):
        data = load_quiz_data(self.test_file_path)
        self.assertIsInstance(data, dict)
        self.assertIn('metadata', data)
        self.assertIn('questions', data)
        self.assertGreater(len(data['questions']), 0)

if __name__ == '__main__':
    unittest.main()
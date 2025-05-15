import unittest
from src.dataset_updater import DatasetUpdater

class TestDatasetUpdater(unittest.TestCase):

    def setUp(self):
        self.updater = DatasetUpdater()
        self.sample_data = {
            "ID": 20,
            "title": "Sample Quiz",
            "image": "images/quiz_info/optimized/",
            "tags": ["数学", "物理"],
            "description": "これはサンプルクイズです。",
            "date": "2025/01/01",
            "category": "science",
            "total_questions": 10,
            "subject": "数学",
            "period": "高校",
            "questions": [
                {
                    "ID": 200,
                    "text": "次の数式の結果は？ 2 + 2 = ?",
                    "choices": ["1", "2", "3", "4"],
                    "correct_choice_id": 4,
                    "explanation": "2 + 2 は 4 です。",
                    "category": "science"
                }
            ]
        }

    def test_add_data(self):
        initial_length = len(self.updater.dataset)
        self.updater.add_data(self.sample_data)
        self.assertEqual(len(self.updater.dataset), initial_length + 1)

    def test_data_integrity(self):
        self.updater.add_data(self.sample_data)
        last_entry = self.updater.dataset[-1]
        self.assertEqual(last_entry["ID"], self.sample_data["ID"])
        self.assertEqual(last_entry["title"], self.sample_data["title"])

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest import mock

from py.repositories import quiz_catalog


class _Snapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    def to_dict(self):
        return dict(self._data)


class _FakeDb:
    def __init__(self, documents):
        self.documents = documents
        self.queries = []

    def collection(self, name):
        self.queries.append(name)
        collection = mock.MagicMock()
        collection.where.return_value.stream.return_value = [
            _Snapshot(doc_id, data) for doc_id, data in self.documents[name]
        ]
        return collection


class QuizCatalogTest(unittest.TestCase):
    def setUp(self):
        quiz_catalog._cache.update(loaded_at=None, quizzes=[], questions=[])
        self.db = _FakeDb({
            'quizzes': [('official-001', {'title': 'Q1', 'status': 'published', 'created_at': object()})],
            'questions': [
                ('official-001-q', {'quiz_id': 'official-001', 'status': 'published', 'text': 'T',
                                    'choices': [], 'correct_choice_id': 1, 'updated_at': object()}),
            ],
        })
        patcher = mock.patch.object(quiz_catalog, 'get_firestore_client', return_value=self.db)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_published_quiz_without_timestamps(self):
        quiz = quiz_catalog.get_quiz('official-001')
        self.assertEqual(quiz['title'], 'Q1')
        self.assertNotIn('created_at', quiz)

    def test_questions_are_filtered_by_quiz_id(self):
        self.assertEqual(len(quiz_catalog.get_published_questions('official-001')), 1)
        self.assertEqual(quiz_catalog.get_published_questions('official-999'), [])
        self.assertIsNotNone(quiz_catalog.get_published_question('official-001-q'))

    def test_results_are_cached(self):
        quiz_catalog.list_quizzes()
        quiz_catalog.get_published_questions('official-001')
        self.assertEqual(self.db.queries, ['quizzes', 'questions'])


if __name__ == '__main__':
    unittest.main()

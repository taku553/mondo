import unittest
from datetime import datetime, timezone
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


CREATED = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


class QuizCatalogTest(unittest.TestCase):
    def setUp(self):
        quiz_catalog._cache.update(loaded_at=None, quizzes=[], questions=[])
        self.db = _FakeDb({
            'quizzes': [
                ('official-001', {'title': 'Q1', 'status': 'published', 'created_at': CREATED,
                                  'author_uid': None, 'moderation': 'none'}),
                ('user-hidden', {'title': 'H', 'status': 'published', 'created_at': CREATED,
                                 'author_uid': 'u1', 'moderation': 'hidden'}),
            ],
            'questions': [
                ('official-001', {'quiz_id': 'official-001', 'status': 'published', 'text': 'T',
                                  'choices': [], 'correct_choice_id': 1, 'updated_at': CREATED}),
                ('user-hidden', {'quiz_id': 'user-hidden', 'status': 'published', 'text': 'H',
                                 'choices': [], 'correct_choice_id': 1}),
            ],
        })
        patcher = mock.patch.object(quiz_catalog, 'get_firestore_client', return_value=self.db)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_published_quiz_with_iso_created_at_and_no_private_fields(self):
        quiz = quiz_catalog.get_quiz('official-001')
        self.assertEqual(quiz['title'], 'Q1')
        self.assertEqual(quiz['created_at'], CREATED.isoformat())
        self.assertNotIn('author_uid', quiz)
        self.assertNotIn('moderation', quiz)

    def test_quiz_exposes_derived_question_count_and_genre_fallback(self):
        quiz = quiz_catalog.get_quiz('official-001')
        self.assertEqual(quiz['question_count'], 1)
        self.assertEqual(quiz['genre'], '')

        quiz_catalog.invalidate_cache()
        self.db.documents['quizzes'][0][1]['genre'] = '江戸'
        self.assertEqual(quiz_catalog.get_quiz('official-001')['genre'], '江戸')

        quiz_catalog.invalidate_cache()
        self.db.documents['quizzes'][0][1].pop('genre')
        self.db.documents['quizzes'][0][1]['subject'] = '戦国'
        self.assertEqual(quiz_catalog.get_quiz('official-001')['genre'], '戦国')

    def test_moderated_quiz_and_its_questions_are_hidden(self):
        self.assertIsNone(quiz_catalog.get_quiz('user-hidden'))
        self.assertEqual(quiz_catalog.get_published_questions('user-hidden'), [])
        self.assertIsNone(quiz_catalog.get_published_question('user-hidden'))
        self.assertEqual([q['id'] for q in quiz_catalog.list_quizzes()], ['official-001'])

    def test_questions_are_filtered_by_quiz_id(self):
        self.assertEqual(len(quiz_catalog.get_published_questions('official-001')), 1)
        self.assertEqual(quiz_catalog.get_published_questions('official-999'), [])
        self.assertIsNotNone(quiz_catalog.get_published_question('official-001'))

    def test_results_are_cached_until_invalidated(self):
        quiz_catalog.list_quizzes()
        quiz_catalog.get_published_questions('official-001')
        self.assertEqual(self.db.queries, ['quizzes', 'questions'])
        quiz_catalog.invalidate_cache()
        quiz_catalog.list_quizzes()
        self.assertEqual(self.db.queries, ['quizzes', 'questions', 'quizzes', 'questions'])


if __name__ == '__main__':
    unittest.main()
